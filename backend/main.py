from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import numpy as np
import base64
import cv2
import time
from typing import Optional, List

import os
import bcrypt
from datetime import datetime
from db.employees_db import (
    add_employees,
    delete_employee,
    update_employee,
    load_employees,
    find_closest_embedding,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models once
face_app = create_face_app()
liveness_detector = LivenessDetector()


@app.on_event("startup")
def startup_event():
    print("STARTING UP DATABASE INITIALIZATION...")
    import db.employees_db
    import db.logs_db

    db.employees_db.init_db()
    db.logs_db.init_db()
    print("DATABASE INITIALIZATION COMPLETE.")


class EmployeeUpdate(BaseModel):
    name: str
    status: str
    start_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None


class EmployeeAdd(EmployeeUpdate):
    embedding: List[float]


@app.get("/api/employees")
def get_employees():
    df = load_employees()
    df = df.replace({np.nan: None})
    for col in df.select_dtypes(include=["datetime64"]).columns:
        df[col] = df[col].astype(object).where(df[col].notnull(), None)
    return df.to_dict(orient="records")


@app.delete("/api/employees/{emp_id}")
def delete_emp(emp_id: int):
    delete_employee(emp_id)
    return {"status": "ok"}


@app.post("/api/login")
def login(credentials: dict):
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
                return {"status": "ok", "token": "authenticated"}  # nosec B105
    except Exception as e:
        print("Error reading secrets:", e)

    raise HTTPException(status_code=401, detail="Invalid login or password")


@app.put("/api/employees/{emp_id}")
def update_emp(emp_id: int, emp: EmployeeUpdate):
    try:
        update_employee(
            emp_id, emp.name, emp.status, emp.start_date, emp.expiration_date
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/employees")
def add_emp(emp: EmployeeAdd):
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
def get_logs(start_date: Optional[str] = None, end_date: Optional[str] = None):
    sd = start_date if start_date else None
    ed = end_date if end_date else None
    return get_all_logs(sd, ed)


@app.websocket("/ws/recognize")
async def websocket_recognize(websocket: WebSocket):
    await websocket.accept()

    unrecognized_frames = 0
    access_granted_until = 0
    last_log_time = 0
    last_logged_name = None
    last_logged_status = None
    log_cooldown = 5.0

    try:
        while True:
            data = await websocket.receive_text()
            current_time = time.time()

            if "," in data:
                data = data.split(",")[1]
            img_data = base64.b64decode(data)
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is None:
                await websocket.send_json({"status": "Error decoding image"})
                continue

            embedding, face, status_code = extract_embedding_from_frame(
                face_app, liveness_detector, img
            )

            response = {
                "status": "No face detected",
                "color": "#888888",
                "name": "-",
                "similarity": "-",
            }

            if status_code == "real" and embedding is not None:
                if last_logged_status != "RECOGNIZING":
                    leds.start_recognizing()
                    last_logged_status = "RECOGNIZING"

                match = find_closest_embedding(embedding)
                if match:
                    unrecognized_frames = 0
                    access_granted_until = current_time + 3.0
                    emp_id, name, similarity = match
                    response = {
                        "status": "Access Granted",
                        "color": "#00FF00",
                        "name": name,
                        "similarity": f"{similarity * 100:.1f}%",
                        "box": face.bbox.tolist(),
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
                                "box": face.bbox.tolist(),
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
                                "box": face.bbox.tolist(),
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

            await websocket.send_json(response)

    except WebSocketDisconnect:
        leds.all_off()


@app.websocket("/ws/enroll")
async def websocket_enroll(websocket: WebSocket):
    await websocket.accept()
    embeddings = []

    try:
        while True:
            data = await websocket.receive_text()

            if len(embeddings) >= 30:
                final_embedding = average_embeddings(embeddings)
                await websocket.send_json(
                    {"status": "Finished", "embedding": final_embedding.tolist()}
                )
                continue

            if "," in data:
                data = data.split(",")[1]
            img_data = base64.b64decode(data)
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is None:
                continue

            embedding, face, status_code = extract_embedding_from_frame(
                face_app, liveness_detector, img
            )
            if status_code == "spoof":
                from faceguard.recognize import get_face_embedding

                embedding = get_face_embedding(face)
                status_code = "real"

            if status_code == "real" and embedding is not None:
                embeddings.append(embedding)
                leds.registration_active()
                await websocket.send_json(
                    {
                        "status": f"Collecting: {len(embeddings)}/30",
                        "color": "#00FF00",
                        "box": face.bbox.tolist(),
                        "progress": len(embeddings) / 30.0,
                    }
                )
            elif status_code == "bad_face":
                await websocket.send_json(
                    {
                        "status": "Look straight",
                        "color": "#00FFFF",
                        "box": face.bbox.tolist(),
                        "progress": len(embeddings) / 30.0,
                    }
                )
            else:
                leds.all_off()
                await websocket.send_json(
                    {
                        "status": "No face detected",
                        "color": "#888888",
                        "box": None,
                        "progress": len(embeddings) / 30.0,
                    }
                )

    except WebSocketDisconnect:
        leds.all_off()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
