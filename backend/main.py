import asyncio
import base64
import binascii
import logging
import os
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from typing import List, Optional

import bcrypt
import cv2
import numpy as np
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from camera import CameraError, CameraFrame, CameraSettings, LatestFrameCamera
from core.security import create_access_token, get_current_user, verify_token
from db.connection import close_pool
from db.employees_db import (
    DuplicateEmployeeError,
    add_employees,
    delete_employee,
    load_employees,
    update_employee,
)
from db.logs_db import add_log, get_all_logs
from faceguard.recognize import (
    InsightFaceProvider,
    LivenessDetector,
    average_embeddings,
    create_face_app,
    extract_embedding_from_frame,
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

camera_settings = CameraSettings.from_env()
camera_factory = LatestFrameCamera
operation_lock = asyncio.Lock()
face_app = None
liveness_detector = None
log_cleanup_task = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    await startup_event()
    try:
        yield
    finally:
        await shutdown_event()


app = FastAPI(lifespan=lifespan)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.state.active_camera = None
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

configured_origins = [
    value.strip()
    for value in os.environ.get("CORS_ORIGINS", "").split(",")
    if value.strip()
]
if not configured_origins:
    configured_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if "*" in configured_origins:
    raise RuntimeError("CORS_ORIGINS must list explicit trusted origins")

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    frame = load_employees().replace({np.nan: None})
    for column in frame.select_dtypes(include=["datetime64"]).columns:
        frame[column] = (
            frame[column].astype(object).where(frame[column].notnull(), None)
        )
    return frame.to_dict(orient="records")


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
    emp_id: int,
    emp: EmployeeUpdate,
    user: dict = Depends(get_current_user),
):
    try:
        update_employee(
            emp_id,
            emp.name,
            emp.status,
            emp.start_date,
            emp.expiration_date,
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
    """Return the newest message currently queued by a browser client."""

    data = await websocket.receive_text()
    while True:
        try:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
        except asyncio.TimeoutError:
            return data


def decode_browser_frame(data: str):
    encoded = data.split(",", maxsplit=1)[1] if "," in data else data
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None
    return cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)


def encode_backend_frame(frame, quality: int) -> str:
    quality_key = getattr(cv2, "IMWRITE_JPEG_QUALITY", 1)
    success, encoded = cv2.imencode(".jpg", frame, [quality_key, int(quality)])
    if not success:
        raise CameraError("Unable to encode backend camera frame as JPEG")
    payload = base64.b64encode(encoded.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


def serialize_box(face):
    if face is None:
        return None
    bbox = face.get("bbox") if isinstance(face, dict) else getattr(face, "bbox", None)
    if bbox is None:
        return None
    values = np.asarray(bbox).reshape(-1)
    if values.size != 4:
        logger.warning("Recognition provider returned an invalid bbox")
        return None
    return [float(value) for value in values]


async def authenticate_websocket(websocket: WebSocket) -> bool:
    offered = [
        value.strip()
        for value in websocket.headers.get("sec-websocket-protocol", "").split(",")
        if value.strip()
    ]
    bearer = next(
        (value for value in offered if value.startswith(WEBSOCKET_BEARER_PREFIX)),
        None,
    )
    if WEBSOCKET_APPLICATION_PROTOCOL not in offered or bearer is None:
        await websocket.close(code=1008)
        return False
    try:
        verify_token(bearer.removeprefix(WEBSOCKET_BEARER_PREFIX))
    except HTTPException:
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


async def next_input_frame(websocket, camera, last_sequence: int):
    if camera_settings.source == "backend":
        return await run_in_threadpool(
            camera.wait_for_frame,
            last_sequence,
            camera_settings.frame_timeout,
        )
    data = await drain_websocket(websocket)
    captured_at = time.perf_counter()
    image = await run_in_threadpool(decode_browser_frame, data)
    if image is None:
        return None
    return CameraFrame(
        sequence=last_sequence + 1,
        captured_at=captured_at,
        image=image,
        capture_ms=0.0,
    )


async def send_frame_response(websocket, response: dict, frame: CameraFrame) -> None:
    height, width = frame.image.shape[:2]
    response["box"] = response.get("box")
    response["frame_width"] = int(width)
    response["frame_height"] = int(height)
    response["frame_sequence"] = frame.sequence
    if camera_settings.source == "backend":
        response["frame"] = await run_in_threadpool(
            encode_backend_frame,
            frame.image,
            camera_settings.jpeg_quality,
        )
    await websocket.send_json(response)


async def run_led(action) -> None:
    try:
        await run_in_threadpool(action)
    except Exception:
        logger.exception("LED action failed: %s", getattr(action, "__name__", action))


async def record_event(name: str, status: str, led_action) -> None:
    try:
        await run_in_threadpool(add_log, name, status)
    except Exception:
        logger.exception("Unable to persist recognition event %s", status)
    await run_led(led_action)


async def send_stream_error(websocket, message: str) -> None:
    with suppress(Exception):
        await websocket.send_json(
            {
                "status": message,
                "color": "#FF0000",
                "box": None,
                "fatal": True,
                "error_code": "stream_error",
            }
        )
    with suppress(Exception):
        await websocket.close(code=1011)


async def cleanup_operation(camera, keep_completion_led: bool = False) -> None:
    try:
        if camera is not None:
            await run_in_threadpool(camera.stop)
            if app.state.active_camera is camera:
                app.state.active_camera = None
        if not keep_completion_led:
            await run_led(leds.all_off)
    finally:
        if operation_lock.locked():
            operation_lock.release()


async def shielded_cleanup(camera, keep_completion_led: bool = False) -> None:
    """Finish releasing owned resources even if the handler is cancelled."""

    cleanup_task = asyncio.create_task(
        cleanup_operation(camera, keep_completion_led=keep_completion_led)
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
    try:
        if face_app is None or liveness_detector is None:
            raise RuntimeError("Recognition models are not initialized")
        await websocket.accept(subprotocol=WEBSOCKET_APPLICATION_PROTOCOL)
        if camera_settings.source == "backend":
            camera = camera_factory(camera_settings)
            app.state.active_camera = camera
            await run_in_threadpool(camera.start)

        from faceguard.business_logic import process_access_attempt

        recognizer = InsightFaceProvider(face_app, liveness_detector)
        last_sequence = 0
        unrecognized_frames = 0
        access_granted_until = 0.0
        last_log_time = 0.0
        last_logged_name = None
        last_logged_status = None
        led_state = None

        while True:
            frame = await next_input_frame(websocket, camera, last_sequence)
            if frame is None:
                await websocket.send_json({"status": "Error decoding image"})
                continue
            last_sequence = frame.sequence
            current_time = time.time()
            access_granted, status_code, name, score, face = await run_in_threadpool(
                process_access_attempt,
                frame=frame.image,
                recognizer=recognizer,
            )
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
                    response.update(
                        status="Access Granted",
                        color="#00FF00",
                        name=name,
                        similarity=f"{score:.1f}%",
                    )
                    if (
                        current_time - last_log_time > 5.0
                        or last_logged_name != name
                        or last_logged_status != "ACCESS_GRANTED"
                    ):
                        await record_event(name, "ACCESS_GRANTED", leds.access_granted)
                        last_log_time = current_time
                        last_logged_name = name
                        last_logged_status = "ACCESS_GRANTED"
                        led_state = "ACCESS_GRANTED"
                elif current_time < access_granted_until:
                    response.update(
                        status="Access Granted",
                        color="#00FF00",
                        name=last_logged_name,
                        similarity="-",
                    )
                else:
                    unrecognized_frames += 1
                    if unrecognized_frames >= 2:
                        response.update(
                            status="Access Denied",
                            color="#FF0000",
                            name="Unknown",
                            similarity="0%",
                        )
                        if (
                            current_time - last_log_time > 5.0
                            or last_logged_name != "UNKNOWN"
                            or last_logged_status != "ACCESS_DENIED"
                        ):
                            await record_event(
                                "UNKNOWN",
                                "ACCESS_DENIED",
                                leds.access_denied,
                            )
                            last_log_time = current_time
                            last_logged_name = "UNKNOWN"
                            last_logged_status = "ACCESS_DENIED"
                            led_state = "ACCESS_DENIED"
                    else:
                        response.update(
                            status="Recognizing...",
                            color="#FFFF00",
                            name="...",
                            similarity="-",
                        )
                        if led_state != "RECOGNIZING":
                            await run_led(leds.start_recognizing)
                            led_state = "RECOGNIZING"
            elif status_code == "spoof" and current_time >= access_granted_until:
                unrecognized_frames = 0
                response.update(
                    status="SPOOF DETECTED",
                    color="#FF0000",
                    name="Unknown",
                    similarity="-",
                )
                if (
                    last_logged_status != "SPOOF_ATTEMPT"
                    or current_time - last_log_time > 5.0
                ):
                    await record_event("UNKNOWN", "SPOOF_ATTEMPT", leds.access_denied)
                    last_log_time = current_time
                    last_logged_name = "UNKNOWN"
                    last_logged_status = "SPOOF_ATTEMPT"
                    led_state = "SPOOF_ATTEMPT"
            elif status_code == "bad_face" and current_time >= access_granted_until:
                unrecognized_frames = 0
                response.update(
                    status="Look straight",
                    color="#00FFFF",
                    name="-",
                    similarity="-",
                )
                if led_state != "BAD_FACE":
                    await run_led(leds.bad_frame)
                    led_state = "BAD_FACE"
            elif current_time >= access_granted_until:
                unrecognized_frames = 0
                if led_state != "NO_FACE":
                    await run_led(leds.all_off)
                    led_state = "NO_FACE"

            await send_frame_response(websocket, response, frame)
    except WebSocketDisconnect:
        pass
    except CameraError:
        logger.exception("Backend recognition camera failed")
        await send_stream_error(websocket, "Backend camera error")
    except Exception:
        logger.exception("Recognition WebSocket failed")
        await send_stream_error(websocket, "Recognition stream error")
    finally:
        await shielded_cleanup(camera)


@app.websocket("/ws/enroll")
async def websocket_enroll(websocket: WebSocket):
    if not await authenticate_websocket(websocket):
        return
    if not await claim_operation(websocket):
        return

    camera = None
    finished = False
    try:
        if face_app is None or liveness_detector is None:
            raise RuntimeError("Recognition models are not initialized")
        await websocket.accept(subprotocol=WEBSOCKET_APPLICATION_PROTOCOL)
        if camera_settings.source == "backend":
            camera = camera_factory(camera_settings)
            app.state.active_camera = camera
            await run_in_threadpool(camera.start)

        embeddings = []
        last_sequence = 0
        enrollment_led_state = None
        while True:
            frame = await next_input_frame(websocket, camera, last_sequence)
            if frame is None:
                await websocket.send_json({"status": "Error decoding image"})
                continue
            last_sequence = frame.sequence
            embedding, face, status_code = await run_in_threadpool(
                extract_embedding_from_frame,
                face_app,
                liveness_detector,
                frame.image,
            )
            box = serialize_box(face)

            if status_code == "real" and embedding is not None:
                embeddings.append(embedding)
                if enrollment_led_state != "REGISTRATION_ACTIVE":
                    await run_led(leds.registration_active)
                    enrollment_led_state = "REGISTRATION_ACTIVE"
                if len(embeddings) == 30:
                    averaged = await run_in_threadpool(average_embeddings, embeddings)
                    await send_frame_response(
                        websocket,
                        {
                            "status": "Finished",
                            "color": "#00FF00",
                            "box": box,
                            "progress": 1.0,
                            "embedding": averaged.tolist(),
                        },
                        frame,
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
            await send_frame_response(websocket, response, frame)
    except WebSocketDisconnect:
        pass
    except CameraError:
        logger.exception("Backend enrollment camera failed")
        await send_stream_error(websocket, "Backend camera error")
    except Exception:
        logger.exception("Enrollment WebSocket failed")
        await send_stream_error(websocket, "Enrollment stream error")
    finally:
        await shielded_cleanup(camera, keep_completion_led=finished)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
