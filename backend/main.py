import asyncio
import base64
import binascii
import logging
import os
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from typing import List, Optional

import runtime  # noqa: F401 - applies native thread limits before NumPy import.
import bcrypt
import cv2
import numpy as np
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Depends,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from core.security import create_access_token, get_current_user, verify_token
from fastapi.concurrency import run_in_threadpool

from camera import CameraError, CameraFrame, CameraSettings, LatestFrameCamera
from db.connection import close_pool
from db.employees_db import (
    DuplicateEmployeeError,
    add_employees,
    delete_employee,
    update_employee,
    load_employees,
)
from db.logs_db import get_all_logs, add_log
from faceguard.recognize import (
    create_face_app,
    LivenessDetector,
    extract_embedding_from_frame,
    average_embeddings,
    InsightFaceProvider,
)
import leds

logger = logging.getLogger(__name__)

WEBSOCKET_APPLICATION_PROTOCOL = "faceguard.jwt"
WEBSOCKET_BEARER_PREFIX = "bearer."
OPERATION_HANDOFF_TIMEOUT_SECONDS = float(
    os.environ.get("OPERATION_HANDOFF_TIMEOUT_SECONDS", "5.0")
)
if OPERATION_HANDOFF_TIMEOUT_SECONDS <= 0:
    raise RuntimeError("OPERATION_HANDOFF_TIMEOUT_SECONDS must be positive")


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        await startup_event()
        yield
    finally:
        await shutdown_event()


app = FastAPI(lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.state.active_camera = None
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

default_cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
configured_cors_origins = os.environ.get("CORS_ORIGINS", "")
cors_origins = [
    origin.strip() for origin in configured_cors_origins.split(",") if origin.strip()
]
if not cors_origins:
    cors_origins = default_cors_origins
if "*" in cors_origins:
    raise RuntimeError("CORS_ORIGINS must list explicit trusted origins")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models are loaded once during startup. Keeping import side effects light lets
# CI exercise the real application boundary without downloading model assets.
face_app = None
liveness_detector = None
camera_settings = CameraSettings.from_env()
camera_factory = LatestFrameCamera
log_cleanup_task = None

# A deployment has one physical entry point and one pair of model sessions.
# Holding this lock for the complete WebSocket operation prevents recognition
# and enrollment from competing for either the USB camera or global inference.
operation_lock = asyncio.Lock()


def initialize_models() -> None:
    global face_app, liveness_detector
    if face_app is None:
        face_app = create_face_app()
    if liveness_detector is None:
        liveness_detector = LivenessDetector()


async def log_cleanup_loop() -> None:
    from db.logs_db import delete_old_logs

    while True:
        try:
            await run_in_threadpool(delete_old_logs)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Periodic access-log cleanup failed")
        await asyncio.sleep(3600)


async def startup_event() -> None:
    global log_cleanup_task
    import db.employees_db
    import db.logs_db

    await run_in_threadpool(db.employees_db.init_db)
    await run_in_threadpool(db.logs_db.init_db)
    await run_in_threadpool(initialize_models)
    if log_cleanup_task is None or log_cleanup_task.done():
        log_cleanup_task = asyncio.create_task(log_cleanup_loop())


async def shutdown_event() -> None:
    global log_cleanup_task
    if log_cleanup_task is not None:
        log_cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await log_cleanup_task
        log_cleanup_task = None
    active_camera = app.state.active_camera
    if active_camera is not None:
        await run_in_threadpool(active_camera.stop)
        app.state.active_camera = None
    await run_in_threadpool(leds.shutdown)
    await run_in_threadpool(close_pool)


class EmployeeUpdate(BaseModel):
    name: str
    status: str
    start_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None


class EmployeeAdd(EmployeeUpdate):
    embedding: List[float]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "camera_source": camera_settings.source,
        "models_ready": face_app is not None and liveness_detector is not None,
        "gpio_available": leds.GPIO_AVAILABLE,
    }


@app.get("/api/employees")
def get_employees(user: dict = Depends(get_current_user)):
    df = load_employees()
    df = df.replace({np.nan: None})
    for col in df.select_dtypes(include=["datetime64"]).columns:
        df[col] = df[col].astype(object).where(df[col].notnull(), None)
    return df.to_dict(orient="records")


@app.delete("/api/employees/{emp_id}")
def delete_emp(emp_id: int, user: dict = Depends(get_current_user)):
    delete_employee(emp_id)
    return {"status": "ok"}


@app.post("/api/login")
@limiter.limit("5/minute")
def login(request: Request, credentials: dict):
    valid_user = os.environ.get("ADMIN_LOGIN", "admin")
    stored_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
    supplied_user = credentials.get("username")
    supplied_password = credentials.get("password", "").encode("utf-8")
    try:
        valid_password = bool(stored_hash) and bcrypt.checkpw(
            supplied_password,
            stored_hash.encode("utf-8"),
        )
    except (TypeError, ValueError):
        logger.warning("ADMIN_PASSWORD_HASH is not a valid bcrypt hash")
        valid_password = False
    if supplied_user == valid_user and valid_password:
        return {"status": "ok", "token": create_access_token({"sub": valid_user})}
    raise HTTPException(status_code=401, detail="Invalid login or password")


@app.put("/api/employees/{emp_id}")
def update_emp(
    emp_id: int, emp: EmployeeUpdate, user: dict = Depends(get_current_user)
):
    try:
        update_employee(
            emp_id, emp.name, emp.status, emp.start_date, emp.expiration_date
        )
        return {"status": "ok"}
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/employees")
def add_emp(emp: EmployeeAdd, user: dict = Depends(get_current_user)):
    try:
        add_employees(
            emp.name,
            emp.status,
            np.asarray(emp.embedding, dtype=np.float32),
            emp.start_date,
            emp.expiration_date,
        )
        return {"status": "ok"}
    except DuplicateEmployeeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/logs")
def get_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    return get_all_logs(start_date or None, end_date or None)


async def drain_websocket(websocket: WebSocket) -> str:
    # Read the first available message
    data = await websocket.receive_text()
    # Keep reading and discarding until the queue is empty
    while True:
        try:
            # timeout=0.001 means it returns almost instantly if queue is empty
            next_data = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
            data = next_data
        except asyncio.TimeoutError:
            break
    return data


def decode_browser_frame(data: str):
    """Decode one browser data URL without doing CPU work on the event loop."""
    encoded = data.split(",", maxsplit=1)[1] if "," in data else data
    try:
        img_data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None
    np_arr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


def encode_backend_frame(frame, quality: int) -> str:
    quality_property = getattr(cv2, "IMWRITE_JPEG_QUALITY", 1)
    success, encoded = cv2.imencode(".jpg", frame, [quality_property, int(quality)])
    if not success:
        raise CameraError("Unable to encode backend camera frame as JPEG")
    payload = base64.b64encode(encoded.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


def serialize_box(face):
    if face is None:
        return None
    if isinstance(face, dict):
        bbox = face.get("bbox")
    else:
        bbox = getattr(face, "bbox", None)
    if bbox is None:
        return None
    values = np.asarray(bbox).reshape(-1)
    if values.size != 4:
        logger.warning("Recognition provider returned an invalid bbox shape")
        return None
    return [float(value) for value in values]


class StreamMetrics:
    """Aggregate per-connection timing without logging frames or credentials."""

    def __init__(self, mode: str):
        self.mode = mode
        self.started_at = time.perf_counter()
        self.last_report_at = self.started_at
        self.frames = 0
        self.capture_ms = 0.0
        self.frame_age_ms = 0.0
        self.inference_ms = 0.0
        self.encode_ms = 0.0
        self.send_ms = 0.0

    def record(
        self,
        frame: CameraFrame,
        inference_ms: float,
        encode_ms: float,
        send_ms: float,
    ) -> None:
        now = time.perf_counter()
        self.frames += 1
        self.capture_ms += frame.capture_ms
        self.frame_age_ms += max(0.0, (now - frame.captured_at) * 1000.0)
        self.inference_ms += inference_ms
        self.encode_ms += encode_ms
        self.send_ms += send_ms
        if now - self.last_report_at >= 5.0:
            self._report(now, final=False)
            self.last_report_at = now

    def _report(self, now: float, final: bool) -> None:
        if self.frames == 0:
            return
        elapsed = max(now - self.started_at, 0.001)
        divisor = float(self.frames)
        logger.info(
            "Camera stream metrics mode=%s final=%s frames=%s fps=%.2f "
            "capture_ms=%.1f frame_age_ms=%.1f inference_ms=%.1f "
            "encode_ms=%.1f send_ms=%.1f",
            self.mode,
            final,
            self.frames,
            self.frames / elapsed,
            self.capture_ms / divisor,
            self.frame_age_ms / divisor,
            self.inference_ms / divisor,
            self.encode_ms / divisor,
            self.send_ms / divisor,
        )

    def finish(self) -> None:
        self._report(time.perf_counter(), final=True)


async def authenticate_websocket(websocket: WebSocket) -> bool:
    offered_protocols = [
        value.strip()
        for value in websocket.headers.get("sec-websocket-protocol", "").split(",")
        if value.strip()
    ]
    token_protocol = next(
        (
            value
            for value in offered_protocols
            if value.startswith(WEBSOCKET_BEARER_PREFIX)
        ),
        None,
    )
    if (
        WEBSOCKET_APPLICATION_PROTOCOL not in offered_protocols
        or token_protocol is None
    ):
        logger.warning("Rejected WebSocket connection without a JWT")
        await websocket.close(code=1008)
        return False
    token = token_protocol[len(WEBSOCKET_BEARER_PREFIX) :]
    try:
        verify_token(token)
    except HTTPException:
        logger.warning("Rejected WebSocket connection with an invalid JWT")
        # Complete the negotiated application handshake before closing so a
        # browser receives 1008 and does not treat auth rejection as a generic
        # 1006 network failure eligible for reconnect.
        await websocket.accept(subprotocol=WEBSOCKET_APPLICATION_PROTOCOL)
        await websocket.close(code=1008)
        return False
    return True


async def claim_operation(websocket: WebSocket) -> bool:
    try:
        await asyncio.wait_for(
            operation_lock.acquire(),
            timeout=OPERATION_HANDOFF_TIMEOUT_SECONDS,
        )
        return True
    except asyncio.TimeoutError:
        await websocket.accept(subprotocol=WEBSOCKET_APPLICATION_PROTOCOL)
        await websocket.send_json(
            {
                "status": "Camera is busy with another operation",
                "color": "#FF0000",
                "box": None,
                "fatal": True,
                "error_code": "operation_busy",
            }
        )
        await websocket.close(code=1013)
        return False


async def next_input_frame(
    websocket: WebSocket,
    camera,
    last_sequence: int,
) -> Optional[CameraFrame]:
    if camera_settings.source == "backend":
        return await run_in_threadpool(
            camera.wait_for_frame,
            last_sequence,
            camera_settings.frame_timeout,
        )

    data = await drain_websocket(websocket)
    started_at = time.perf_counter()
    image = await run_in_threadpool(decode_browser_frame, data)
    if image is None:
        return None
    return CameraFrame(
        sequence=last_sequence + 1,
        captured_at=started_at,
        image=image,
        capture_ms=0.0,
    )


async def send_frame_response(
    websocket: WebSocket,
    response: dict,
    frame: CameraFrame,
    metrics: StreamMetrics,
    inference_ms: float,
) -> None:
    height, width = frame.image.shape[:2]
    response["box"] = response.get("box")
    response["frame_width"] = int(width)
    response["frame_height"] = int(height)
    response["frame_sequence"] = frame.sequence

    encode_ms = 0.0
    if camera_settings.source == "backend":
        encode_started = time.perf_counter()
        response["frame"] = await run_in_threadpool(
            encode_backend_frame, frame.image, camera_settings.jpeg_quality
        )
        encode_ms = (time.perf_counter() - encode_started) * 1000.0

    send_started = time.perf_counter()
    await websocket.send_json(response)
    send_ms = (time.perf_counter() - send_started) * 1000.0
    metrics.record(frame, inference_ms, encode_ms, send_ms)


async def run_led(action) -> None:
    try:
        await run_in_threadpool(action)
    except Exception:
        logger.exception("LED action failed: %s", getattr(action, "__name__", action))


async def record_event(name: str, status: str, led_action) -> None:
    try:
        await run_in_threadpool(add_log, name, status)
    except Exception:
        logger.exception("Unable to persist recognition event status=%s", status)
    await run_led(led_action)


async def send_stream_error(websocket: WebSocket, status: str) -> None:
    try:
        await websocket.send_json(
            {
                "status": status,
                "color": "#FF0000",
                "box": None,
                "fatal": True,
                "error_code": "stream_error",
            }
        )
    except Exception:
        logger.debug("Unable to send WebSocket error response", exc_info=True)


async def close_stream(websocket: WebSocket, code: int) -> None:
    try:
        await websocket.close(code=code)
    except Exception:
        logger.debug("Unable to close WebSocket cleanly", exc_info=True)


async def cleanup_operation(
    camera,
    metrics: Optional[StreamMetrics],
    turn_leds_off: bool,
) -> None:
    """Release an operation even when its request task is cancelled."""
    try:
        if camera is not None:
            try:
                await run_in_threadpool(camera.stop)
            except Exception:
                logger.exception("Unable to stop backend camera cleanly")
            if app.state.active_camera is camera:
                app.state.active_camera = None
        if metrics is not None:
            metrics.finish()
        if turn_leds_off:
            await run_led(leds.all_off)
    finally:
        if operation_lock.locked():
            operation_lock.release()


async def shielded_cleanup(
    camera,
    metrics: Optional[StreamMetrics],
    turn_leds_off: bool,
) -> None:
    cleanup_task = asyncio.create_task(
        cleanup_operation(camera, metrics, turn_leds_off)
    )
    try:
        await asyncio.shield(cleanup_task)
    except asyncio.CancelledError:
        await cleanup_task
        raise


@app.websocket("/ws/recognize")
async def websocket_recognize(websocket: WebSocket):
    if not await authenticate_websocket(websocket):
        return
    if not await claim_operation(websocket):
        return

    camera = None
    metrics = None
    try:
        if face_app is None or liveness_detector is None:
            raise RuntimeError("Recognition models are not initialized")
        unrecognized_frames = 0
        access_granted_until = 0
        last_log_time = 0
        last_logged_name = None
        last_logged_status = None
        led_state = None
        log_cooldown = 5.0
        from faceguard.business_logic import process_access_attempt

        recognizer = InsightFaceProvider(face_app, liveness_detector)
        metrics = StreamMetrics(camera_settings.source)
        last_sequence = 0

        await websocket.accept(subprotocol=WEBSOCKET_APPLICATION_PROTOCOL)
        if camera_settings.source == "backend":
            camera = camera_factory(camera_settings)
            app.state.active_camera = camera
            await run_in_threadpool(camera.start)

        while True:
            frame = await next_input_frame(websocket, camera, last_sequence)
            if frame is None:
                await websocket.send_json({"status": "Error decoding image"})
                continue
            last_sequence = frame.sequence
            current_time = time.time()
            inference_started = time.perf_counter()
            access_granted, status_code, name, score, face = await run_in_threadpool(
                process_access_attempt, frame=frame.image, recognizer=recognizer
            )
            inference_ms = (time.perf_counter() - inference_started) * 1000.0
            box = serialize_box(face)

            response = {
                "status": "No face detected",
                "color": "#888888",
                "name": "-",
                "similarity": "-",
                "box": box,
            }

            if status_code in ("real", "Access Denied"):
                if access_granted:
                    unrecognized_frames = 0
                    access_granted_until = current_time + 3.0
                    response = {
                        "status": "Access Granted",
                        "color": "#00FF00",
                        "name": name,
                        "similarity": f"{score:.1f}%",
                        "box": box,
                    }
                    if (
                        current_time - last_log_time > log_cooldown
                        or last_logged_name != name
                        or last_logged_status != "ACCESS_GRANTED"
                    ):
                        await record_event(name, "ACCESS_GRANTED", leds.access_granted)
                        last_log_time = current_time
                        last_logged_name = name
                        last_logged_status = "ACCESS_GRANTED"
                        led_state = "ACCESS_GRANTED"
                else:
                    if current_time < access_granted_until:
                        response = {
                            "status": "Access Granted",
                            "color": "#00FF00",
                            "name": last_logged_name,
                            "similarity": "-",
                            "box": box,
                        }
                    else:
                        unrecognized_frames += 1
                        if unrecognized_frames >= 2:
                            response = {
                                "status": "Access Denied",
                                "color": "#FF0000",
                                "name": "Unknown",
                                "similarity": "0%",
                                "box": box,
                            }
                            if (
                                current_time - last_log_time > log_cooldown
                                or last_logged_name != "UNKNOWN"
                                or last_logged_status != "ACCESS_DENIED"
                            ):
                                await record_event(
                                    "UNKNOWN", "ACCESS_DENIED", leds.access_denied
                                )
                                last_log_time = current_time
                                last_logged_name = "UNKNOWN"
                                last_logged_status = "ACCESS_DENIED"
                                led_state = "ACCESS_DENIED"
                        else:
                            response = {
                                "status": "Recognizing...",
                                "color": "#FFFF00",
                                "name": "...",
                                "similarity": "-",
                                "box": box,
                            }
                            if led_state != "RECOGNIZING":
                                await run_led(leds.start_recognizing)
                                led_state = "RECOGNIZING"
            elif status_code == "spoof":
                if current_time < access_granted_until:
                    pass
                else:
                    unrecognized_frames = 0
                    response = {
                        "status": "SPOOF DETECTED",
                        "color": "#FF0000",
                        "name": "Unknown",
                        "similarity": "-",
                        "box": box,
                    }
                    if (
                        current_time - last_log_time > log_cooldown
                        or last_logged_status != "SPOOF_ATTEMPT"
                    ):
                        await record_event(
                            "UNKNOWN", "SPOOF_ATTEMPT", leds.access_denied
                        )
                        last_log_time = current_time
                        last_logged_name = "UNKNOWN"
                        last_logged_status = "SPOOF_ATTEMPT"
                        led_state = "SPOOF_ATTEMPT"
            elif status_code == "bad_face":
                if current_time < access_granted_until:
                    pass
                else:
                    unrecognized_frames = 0
                    response = {
                        "status": "Look straight",
                        "color": "#00FFFF",
                        "name": "-",
                        "similarity": "-",
                        "box": box,
                    }
                    if led_state != "BAD_FACE":
                        await run_led(leds.bad_frame)
                        led_state = "BAD_FACE"
            else:
                if current_time >= access_granted_until:
                    unrecognized_frames = 0
                    if led_state != "NO_FACE":
                        await run_led(leds.all_off)
                        led_state = "NO_FACE"

            await send_frame_response(websocket, response, frame, metrics, inference_ms)

    except WebSocketDisconnect:
        pass
    except CameraError as error:
        logger.error("Backend camera stream failed: %s", error)
        await send_stream_error(websocket, "Backend camera error")
        await close_stream(websocket, 1011)
    except Exception:
        logger.exception("Recognition WebSocket failed")
        await send_stream_error(websocket, "Recognition stream error")
        await close_stream(websocket, 1011)
    finally:
        await shielded_cleanup(camera, metrics, turn_leds_off=True)


@app.websocket("/ws/enroll")
async def websocket_enroll(websocket: WebSocket):
    if not await authenticate_websocket(websocket):
        return
    if not await claim_operation(websocket):
        return

    camera = None
    metrics = None
    finished = False
    try:
        if face_app is None or liveness_detector is None:
            raise RuntimeError("Recognition models are not initialized")
        embeddings = []
        metrics = StreamMetrics(camera_settings.source)
        last_sequence = 0
        enrollment_led_state = None

        await websocket.accept(subprotocol=WEBSOCKET_APPLICATION_PROTOCOL)
        if camera_settings.source == "backend":
            camera = camera_factory(camera_settings)
            app.state.active_camera = camera
            await run_in_threadpool(camera.start)

        while True:
            frame = await next_input_frame(websocket, camera, last_sequence)
            if frame is None:
                await websocket.send_json({"status": "Error decoding image"})
                continue
            last_sequence = frame.sequence

            inference_started = time.perf_counter()
            embedding, face, status_code = await run_in_threadpool(
                extract_embedding_from_frame,
                face_app,
                liveness_detector,
                frame.image,
            )
            inference_ms = (time.perf_counter() - inference_started) * 1000.0
            box = serialize_box(face)

            if status_code == "real" and embedding is not None:
                embeddings.append(embedding)
                if enrollment_led_state != "REGISTRATION_ACTIVE":
                    await run_led(leds.registration_active)
                    enrollment_led_state = "REGISTRATION_ACTIVE"
                if len(embeddings) == 30:
                    final_embedding = await run_in_threadpool(
                        average_embeddings, embeddings
                    )
                    response = {
                        "status": "Finished",
                        "color": "#00FF00",
                        "box": box,
                        "progress": 1.0,
                        "embedding": final_embedding.tolist(),
                    }
                    await send_frame_response(
                        websocket, response, frame, metrics, inference_ms
                    )
                    await run_led(leds.registration_done)
                    finished = True
                    return
                response = {
                    "status": f"Collecting: {len(embeddings)}/30",
                    "color": "#00FF00",
                    "box": box,
                    "progress": len(embeddings) / 30.0,
                }
            elif status_code == "spoof":
                if enrollment_led_state != "SPOOF":
                    await run_led(leds.access_denied)
                    enrollment_led_state = "SPOOF"
                response = {
                    "status": "SPOOF DETECTED",
                    "color": "#FF0000",
                    "box": box,
                    "progress": len(embeddings) / 30.0,
                }
            elif status_code == "bad_face":
                if enrollment_led_state != "BAD_FRAME":
                    await run_led(leds.bad_frame)
                    enrollment_led_state = "BAD_FRAME"
                response = {
                    "status": "Look straight",
                    "color": "#00FFFF",
                    "box": box,
                    "progress": len(embeddings) / 30.0,
                }
            else:
                if enrollment_led_state != "OFF":
                    await run_led(leds.all_off)
                    enrollment_led_state = "OFF"
                response = {
                    "status": "No face detected",
                    "color": "#888888",
                    "box": None,
                    "progress": len(embeddings) / 30.0,
                }

            await send_frame_response(websocket, response, frame, metrics, inference_ms)

    except WebSocketDisconnect:
        pass
    except CameraError as error:
        logger.error("Backend enrollment camera stream failed: %s", error)
        await send_stream_error(websocket, "Backend camera error")
        await close_stream(websocket, 1011)
    except Exception:
        logger.exception("Enrollment WebSocket failed")
        await send_stream_error(websocket, "Enrollment stream error")
        await close_stream(websocket, 1011)
    finally:
        await shielded_cleanup(camera, metrics, turn_leds_off=not finished)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
