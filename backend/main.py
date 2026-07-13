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

import numpy as np
import base64
import cv2
import time
from typing import Optional, List
import asyncio
from fastapi.concurrency import run_in_threadpool

import os
import bcrypt
from datetime import datetime
from db.employees_db import (
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
)
import leds

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models once
face_app = create_face_app()
liveness_detector = LivenessDetector()


def _camera_source_from_environment() -> str:
    source = os.environ.get("CAMERA_SOURCE", "browser").strip().lower()
    if source not in {"browser", "backend"}:
        print(f"Unknown CAMERA_SOURCE={source!r}; falling back to browser")
        return "browser"
    return source


def _camera_index_from_environment() -> int:
    value = os.environ.get("CAMERA_INDEX", "0")
    try:
        return int(value)
    except ValueError:
        print(f"Invalid CAMERA_INDEX={value!r}; falling back to 0")
        return 0


CAMERA_SOURCE = _camera_source_from_environment()
CAMERA_INDEX = _camera_index_from_environment()
CAMERA_READ_RETRY_DELAY = 0.1
camera_lock = asyncio.Lock()


class CameraOpenError(RuntimeError):
    pass


class BackendCameraSession:
    """Own one exclusive, short-lived connection to the backend camera."""

    def __init__(self, camera_index: int):
        self.camera_index = camera_index
        self.capture = None
        self.owns_lock = False

    async def acquire(self):
        await camera_lock.acquire()
        self.owns_lock = True
        try:
            self.capture = await run_in_threadpool(cv2.VideoCapture, self.camera_index)
            if self.capture is None or not await run_in_threadpool(
                self.capture.isOpened
            ):
                raise CameraOpenError(
                    f"Unable to open backend camera index {self.camera_index}"
                )

            if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
                try:
                    await run_in_threadpool(
                        self.capture.set, cv2.CAP_PROP_BUFFERSIZE, 1
                    )
                except Exception as exc:
                    print(f"Could not set camera buffer size: {exc}")
            return self
        except Exception:
            await self.close()
            raise

    async def read(self):
        success, frame = await run_in_threadpool(self.capture.read)
        if not success or frame is None:
            await asyncio.sleep(CAMERA_READ_RETRY_DELAY)
            return None
        return frame

    async def close(self):
        try:
            if self.capture is not None:
                try:
                    await run_in_threadpool(self.capture.release)
                except Exception as exc:
                    print(f"Could not release backend camera: {exc}")
        finally:
            self.capture = None
            if self.owns_lock:
                self.owns_lock = False
                camera_lock.release()


def decode_browser_frame(data: str):
    if "," in data:
        data = data.split(",", 1)[1]
    img_data = base64.b64decode(data)
    np_arr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


def encode_preview_frame(frame) -> Optional[str]:
    success, encoded = cv2.imencode(".jpg", frame)
    if not success:
        return None
    payload = base64.b64encode(encoded.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


@app.on_event("startup")
def startup_event():
    print("STARTING UP DATABASE INITIALIZATION...")
    import db.employees_db
    import db.logs_db

    db.employees_db.init_db()
    db.logs_db.init_db()
    print("DATABASE INITIALIZATION COMPLETE.")


@app.on_event("shutdown")
def shutdown_event():
    leds.cleanup()


class EmployeeUpdate(BaseModel):
    name: str
    status: str
    start_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None


class EmployeeAdd(EmployeeUpdate):
    embedding: List[float]


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
    try:
        from dotenv import load_dotenv

        load_dotenv()

        valid_user = os.environ.get("ADMIN_LOGIN", "admin")
        stored_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")

        provided_username = credentials.get("username")
        provided_password = credentials.get("password", "").encode("utf-8")

        if provided_username == valid_user and stored_hash:
            # Check bcrypt hash
            if bcrypt.checkpw(provided_password, stored_hash.encode("utf-8")):
                token = create_access_token({"sub": valid_user})
                return {"status": "ok", "token": token}  # nosec B105
    except Exception as e:
        print("Error reading secrets:", e)

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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/employees")
def add_emp(emp: EmployeeAdd, user: dict = Depends(get_current_user)):
    try:
        add_employees(
            emp.name,
            emp.status,
            np.array(emp.embedding),
            emp.start_date,
            emp.expiration_date,
        )
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/logs")
def get_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    sd = start_date if start_date else None
    ed = end_date if end_date else None
    return get_all_logs(sd, ed)


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


@app.websocket("/ws/recognize")
async def websocket_recognize(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    unrecognized_frames = 0
    access_granted_until = 0
    last_log_time = 0
    last_logged_name = None
    last_logged_status = None
    log_cooldown = 5.0

    from faceguard.recognize import InsightFaceProvider
    from faceguard.business_logic import process_access_attempt

    recognizer = InsightFaceProvider(face_app, liveness_detector)
    camera_session = None

    try:
        if CAMERA_SOURCE == "backend":
            camera_session = BackendCameraSession(CAMERA_INDEX)
            await camera_session.acquire()

        while True:
            preview_frame = None
            if CAMERA_SOURCE == "backend":
                img = await camera_session.read()
                if img is None:
                    await websocket.send_json(
                        {
                            "status": "Camera frame unavailable",
                            "color": "#FF0000",
                            "name": "-",
                            "similarity": "-",
                        }
                    )
                    continue
                preview_frame = await run_in_threadpool(encode_preview_frame, img)
                if preview_frame is None:
                    await asyncio.sleep(CAMERA_READ_RETRY_DELAY)
                    await websocket.send_json(
                        {
                            "status": "Error encoding camera frame",
                            "color": "#FF0000",
                            "name": "-",
                            "similarity": "-",
                        }
                    )
                    continue
            else:
                data = await drain_websocket(websocket)
                try:
                    img = await run_in_threadpool(decode_browser_frame, data)
                except Exception:
                    img = None

            current_time = time.time()

            if img is None:
                await websocket.send_json({"status": "Error decoding image"})
                continue

            access_granted, status_code, name, score, face = await run_in_threadpool(
                process_access_attempt, frame=img, recognizer=recognizer
            )

            response = {
                "status": "No face detected",
                "color": "#888888",
                "name": "-",
                "similarity": "-",
            }

            if status_code in ("real", "Access Denied"):
                if last_logged_status != "RECOGNIZING":
                    leds.start_recognizing()
                    last_logged_status = "RECOGNIZING"

                if access_granted:
                    unrecognized_frames = 0
                    access_granted_until = current_time + 3.0
                    response = {
                        "status": "Access Granted",
                        "color": "#00FF00",
                        "name": name,
                        "similarity": f"{score:.1f}%",
                        "box": face.bbox.tolist() if face is not None else None,
                    }
                    if (
                        current_time - last_log_time > log_cooldown
                        or last_logged_name != name
                        or last_logged_status != "ACCESS_GRANTED"
                    ):
                        leds.access_granted()
                        try:
                            add_log(name, "ACCESS_GRANTED")
                            last_log_time = current_time
                            last_logged_name = name
                            last_logged_status = "ACCESS_GRANTED"
                        except Exception as e:
                            print(f"Log error: {e}")
                else:
                    if current_time < access_granted_until:
                        response = {
                            "status": "Access Granted",
                            "color": "#00FF00",
                            "name": last_logged_name,
                            "similarity": "-",
                            "box": face.bbox.tolist() if face is not None else None,
                        }
                    else:
                        unrecognized_frames += 1
                        if unrecognized_frames >= 2:
                            response = {
                                "status": "Access Denied",
                                "color": "#FF0000",
                                "name": "Unknown",
                                "similarity": "0%",
                                "box": face.bbox.tolist() if face is not None else None,
                            }
                            if (
                                current_time - last_log_time > log_cooldown
                                or last_logged_name != "UNKNOWN"
                                or last_logged_status != "ACCESS_DENIED"
                            ):
                                leds.access_denied()
                                try:
                                    add_log("UNKNOWN", "ACCESS_DENIED")
                                    last_log_time = current_time
                                    last_logged_name = "UNKNOWN"
                                    last_logged_status = "ACCESS_DENIED"
                                except Exception as e:
                                    print(f"Log error: {e}")
                        else:
                            response = {
                                "status": "Recognizing...",
                                "color": "#FFFF00",
                                "name": "...",
                                "similarity": "-",
                                "box": face.bbox.tolist() if face is not None else None,
                            }
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
                        "box": face.bbox.tolist() if face is not None else None,
                    }
                    if (
                        current_time - last_log_time > log_cooldown
                        or last_logged_status != "SPOOF_ATTEMPT"
                    ):
                        leds.access_denied()
                        try:
                            add_log("UNKNOWN", "SPOOF_ATTEMPT")
                            last_log_time = current_time
                            last_logged_name = "UNKNOWN"
                            last_logged_status = "SPOOF_ATTEMPT"
                        except Exception as e:
                            print(f"Log error: {e}")
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
                        "box": face.bbox.tolist() if face is not None else None,
                    }
                    if last_logged_status != "BAD_FACE":
                        leds.bad_frame()
                        last_logged_status = "BAD_FACE"
            else:
                if current_time >= access_granted_until:
                    unrecognized_frames = 0
                    if last_logged_status != "NO_FACE":
                        leds.all_off()
                        last_logged_status = "NO_FACE"

            if preview_frame is not None:
                response["frame"] = preview_frame
            await websocket.send_json(response)

    except CameraOpenError as exc:
        await websocket.send_json(
            {
                "status": str(exc),
                "color": "#FF0000",
                "name": "-",
                "similarity": "-",
            }
        )
    except WebSocketDisconnect:
        pass
    finally:
        if camera_session is not None:
            await camera_session.close()
        leds.all_off()


@app.websocket("/ws/enroll")
async def websocket_enroll(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    embeddings = []
    camera_session = None
    last_preview_frame = None

    try:
        if CAMERA_SOURCE == "backend":
            camera_session = BackendCameraSession(CAMERA_INDEX)
            await camera_session.acquire()

        while True:
            if len(embeddings) >= 30:
                final_embedding = await run_in_threadpool(
                    average_embeddings, embeddings
                )
                response = {
                    "status": "Finished",
                    "embedding": final_embedding.tolist(),
                }
                if last_preview_frame is not None:
                    response["frame"] = last_preview_frame
                await websocket.send_json(response)
                return

            preview_frame = None
            if CAMERA_SOURCE == "backend":
                img = await camera_session.read()
                if img is None:
                    await websocket.send_json(
                        {
                            "status": "Camera frame unavailable",
                            "color": "#FF0000",
                            "box": None,
                            "progress": len(embeddings) / 30.0,
                        }
                    )
                    continue
                preview_frame = await run_in_threadpool(encode_preview_frame, img)
                if preview_frame is None:
                    await asyncio.sleep(CAMERA_READ_RETRY_DELAY)
                    await websocket.send_json(
                        {
                            "status": "Error encoding camera frame",
                            "color": "#FF0000",
                            "box": None,
                            "progress": len(embeddings) / 30.0,
                        }
                    )
                    continue
                last_preview_frame = preview_frame
            else:
                data = await drain_websocket(websocket)
                try:
                    img = await run_in_threadpool(decode_browser_frame, data)
                except Exception:
                    img = None

            if img is None:
                continue

            embedding, face, status_code = await run_in_threadpool(
                extract_embedding_from_frame, face_app, liveness_detector, img
            )
            if status_code == "real" and embedding is not None:
                embeddings.append(embedding)
                leds.registration_active()
                response = {
                    "status": f"Collecting: {len(embeddings)}/30",
                    "color": "#00FF00",
                    "box": face.bbox.tolist(),
                    "progress": len(embeddings) / 30.0,
                }
            elif status_code == "spoof":
                response = {
                    "status": "SPOOF DETECTED",
                    "color": "#FF0000",
                    "box": face.bbox.tolist() if face is not None else None,
                    "progress": len(embeddings) / 30.0,
                }
            elif status_code == "bad_face":
                response = {
                    "status": "Look straight",
                    "color": "#00FFFF",
                    "box": face.bbox.tolist(),
                    "progress": len(embeddings) / 30.0,
                }
            else:
                leds.all_off()
                response = {
                    "status": "No face detected",
                    "color": "#888888",
                    "box": None,
                    "progress": len(embeddings) / 30.0,
                }

            if preview_frame is not None:
                response["frame"] = preview_frame
            await websocket.send_json(response)

    except CameraOpenError as exc:
        await websocket.send_json(
            {
                "status": str(exc),
                "color": "#FF0000",
                "box": None,
                "progress": len(embeddings) / 30.0,
            }
        )
    except WebSocketDisconnect:
        pass
    finally:
        if camera_session is not None:
            await camera_session.close()
        leds.all_off()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
