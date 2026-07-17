import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import numpy as np
import pytest

import main as backend_main
from core import security


class FakeWebSocket:
    def __init__(self, token="test-token"):
        self.headers = {"sec-websocket-protocol": f"faceguard.jwt, bearer.{token}"}
        self.accepted = False
        self.accepted_subprotocol = None
        self.sent = []
        self.closed_codes = []

    async def accept(self, subprotocol=None):
        self.accepted = True
        self.accepted_subprotocol = subprotocol

    async def send_json(self, value):
        self.sent.append(value)

    async def close(self, code=None):
        self.closed_codes.append(code)


@pytest.fixture(autouse=True)
def reset_runtime(monkeypatch):
    async def run_inline(function, *args, **kwargs):
        return function(*args, **kwargs)

    # Unit tests exercise orchestration deterministically. The real AnyIO
    # worker-pool boundary is covered by application-boundary integration tests.
    monkeypatch.setattr(backend_main, "run_in_threadpool", run_inline)
    monkeypatch.setattr(backend_main, "operation_lock", asyncio.Lock())
    monkeypatch.setattr(
        backend_main,
        "camera_settings",
        backend_main.CameraSettings(source="browser"),
    )
    monkeypatch.setattr(backend_main, "face_app", object())
    monkeypatch.setattr(backend_main, "liveness_detector", object())
    monkeypatch.setattr(backend_main, "log_cleanup_task", None)
    monkeypatch.setattr(backend_main.app.state, "active_camera", None)
    monkeypatch.setattr(backend_main, "verify_token", lambda token: {"sub": "admin"})


def test_startup_and_shutdown_manage_owned_resources(monkeypatch):
    import db.employees_db
    import db.logs_db

    calls = []
    monkeypatch.setattr(db.employees_db, "init_db", lambda: calls.append("employees"))
    monkeypatch.setattr(db.logs_db, "init_db", lambda: calls.append("logs"))
    monkeypatch.setattr(
        backend_main, "initialize_models", lambda: calls.append("models")
    )
    monkeypatch.setattr(backend_main.leds, "shutdown", lambda: calls.append("gpio"))
    monkeypatch.setattr(backend_main, "close_pool", lambda: calls.append("pool"))

    async def dormant_cleanup():
        await asyncio.Event().wait()

    monkeypatch.setattr(backend_main, "log_cleanup_loop", dormant_cleanup)

    async def scenario():
        await backend_main.startup_event()
        assert backend_main.log_cleanup_task is not None
        await backend_main.shutdown_event()

    asyncio.run(scenario())

    assert calls == ["employees", "logs", "models", "gpio", "pool"]
    assert backend_main.log_cleanup_task is None


def test_shutdown_stops_active_camera_even_without_websocket_cleanup(monkeypatch):
    calls = []
    camera = SimpleNamespace(stop=lambda: calls.append("camera"))
    backend_main.app.state.active_camera = camera
    monkeypatch.setattr(backend_main.leds, "shutdown", lambda: calls.append("gpio"))
    monkeypatch.setattr(backend_main, "close_pool", lambda: calls.append("pool"))

    asyncio.run(backend_main.shutdown_event())

    assert calls == ["camera", "gpio", "pool"]
    assert backend_main.app.state.active_camera is None


def test_employee_endpoint_maps_duplicate_to_conflict(monkeypatch):
    employee = backend_main.EmployeeAdd(
        name="Duplicate",
        status="Permanent",
        embedding=[1.0, 0.0],
    )
    monkeypatch.setattr(
        backend_main,
        "add_employees",
        lambda *args: (_ for _ in ()).throw(
            backend_main.DuplicateEmployeeError("Face already registered as Alice")
        ),
    )

    with pytest.raises(backend_main.HTTPException) as error:
        backend_main.add_emp(employee, user={"sub": "admin"})

    assert error.value.status_code == 409
    assert error.value.detail == "Face already registered as Alice"


def test_login_checks_bcrypt_and_returns_real_signed_token(monkeypatch):
    monkeypatch.setenv("ADMIN_LOGIN", "operator")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "$2b$test")
    monkeypatch.setattr(
        backend_main.bcrypt,
        "checkpw",
        lambda supplied, stored: supplied == b"secret" and stored == b"$2b$test",
    )

    request = backend_main.Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/login",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
    )
    result = backend_main.login(
        request,
        {"username": "operator", "password": "secret"},
    )

    assert result["status"] == "ok"
    decoded = jwt.decode(
        result["token"],
        security.SECRET_KEY,
        algorithms=["HS256"],
    )
    assert decoded["sub"] == "operator"


def test_login_rejects_invalid_or_misconfigured_credentials(monkeypatch):
    monkeypatch.setenv("ADMIN_LOGIN", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "invalid")
    monkeypatch.setattr(
        backend_main.bcrypt,
        "checkpw",
        lambda *args: (_ for _ in ()).throw(ValueError("bad hash")),
    )

    request = backend_main.Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/login",
            "headers": [],
            "client": ("127.0.0.2", 12345),
        }
    )
    with pytest.raises(backend_main.HTTPException) as error:
        backend_main.login(request, {"username": "admin", "password": "x"})

    assert error.value.status_code == 401


def test_drain_websocket_discards_queued_stale_frames():
    class QueuedWebSocket:
        def __init__(self):
            self.messages = ["stale", "latest"]

        async def receive_text(self):
            if self.messages:
                return self.messages.pop(0)
            await asyncio.Event().wait()

    result = asyncio.run(backend_main.drain_websocket(QueuedWebSocket()))

    assert result == "latest"


def test_websocket_rejects_missing_or_invalid_jwt(monkeypatch):
    missing = FakeWebSocket()
    missing.headers = {}
    assert asyncio.run(backend_main.authenticate_websocket(missing)) is False
    assert missing.accepted is False
    assert missing.closed_codes == [1008]

    invalid = FakeWebSocket()
    monkeypatch.setattr(
        backend_main,
        "verify_token",
        lambda token: (_ for _ in ()).throw(
            backend_main.HTTPException(status_code=401, detail="invalid")
        ),
    )
    assert asyncio.run(backend_main.authenticate_websocket(invalid)) is False
    assert invalid.accepted_subprotocol == "faceguard.jwt"
    assert invalid.closed_codes == [1008]


def test_websocket_accepts_a_valid_signed_jwt(monkeypatch):
    secret = "unit-test-websocket-secret-at-least-32-bytes"
    token = jwt.encode(
        {
            "sub": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )
    websocket = FakeWebSocket(token)
    monkeypatch.setattr(
        backend_main,
        "verify_token",
        lambda value: jwt.decode(value, secret, algorithms=["HS256"]),
    )

    assert asyncio.run(backend_main.authenticate_websocket(websocket)) is True


def _one_frame_then_disconnect(monkeypatch, image):
    calls = 0

    async def next_frame(websocket, camera, last_sequence):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise backend_main.WebSocketDisconnect()
        return backend_main.CameraFrame(1, 0.0, image, 0.0)

    monkeypatch.setattr(backend_main, "next_input_frame", next_frame)


def test_recognition_response_keeps_box_and_dimensions_with_processed_frame(
    monkeypatch,
):
    import faceguard.business_logic

    image = np.zeros((4, 6, 3), dtype=np.uint8)
    face = SimpleNamespace(bbox=np.array([1, 1, 5, 3], dtype=np.float32))
    websocket = FakeWebSocket()
    _one_frame_then_disconnect(monkeypatch, image)
    monkeypatch.setattr(
        faceguard.business_logic,
        "process_access_attempt",
        lambda **kwargs: (True, "real", "Alice", 98.5, face),
    )
    logs = []
    leds = []
    monkeypatch.setattr(backend_main, "add_log", lambda *args: logs.append(args))
    monkeypatch.setattr(
        backend_main.leds, "access_granted", lambda: leds.append("blue")
    )
    monkeypatch.setattr(backend_main.leds, "all_off", lambda: leds.append("off"))

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.sent == [
        {
            "status": "Access Granted",
            "color": "#00FF00",
            "name": "Alice",
            "similarity": "98.5%",
            "box": [1.0, 1.0, 5.0, 3.0],
            "frame_width": 6,
            "frame_height": 4,
            "frame_sequence": 1,
        }
    ]
    assert logs == [("Alice", "ACCESS_GRANTED")]
    assert leds == ["blue", "off"]


def test_backend_mode_starts_one_camera_and_returns_matching_jpeg(monkeypatch):
    import faceguard.business_logic

    image = np.zeros((4, 6, 3), dtype=np.uint8)
    websocket = FakeWebSocket()
    events = []

    class FakeCamera:
        def start(self):
            events.append("start")

        def wait_for_frame(self, after_sequence, timeout):
            if after_sequence:
                raise backend_main.WebSocketDisconnect()
            return backend_main.CameraFrame(1, 0.0, image, 0.0)

        def stop(self):
            events.append("stop")

    monkeypatch.setattr(
        backend_main,
        "camera_settings",
        backend_main.CameraSettings(source="backend"),
    )
    monkeypatch.setattr(backend_main, "camera_factory", lambda settings: FakeCamera())
    monkeypatch.setattr(
        faceguard.business_logic,
        "process_access_attempt",
        lambda **kwargs: (False, "no_face", "Unknown", 0.0, None),
    )
    monkeypatch.setattr(
        backend_main,
        "encode_backend_frame",
        lambda frame, quality: "data:image/jpeg;base64,exact-frame",
    )
    monkeypatch.setattr(backend_main.leds, "all_off", lambda: None)

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert events == ["start", "stop"]
    assert websocket.sent[0]["frame"] == "data:image/jpeg;base64,exact-frame"
    assert websocket.sent[0]["frame_width"] == 6
    assert websocket.sent[0]["frame_height"] == 4
    assert websocket.sent[0]["box"] is None


def test_enrollment_finishes_once_and_preserves_completion_feedback(monkeypatch):
    websocket = FakeWebSocket()
    image = np.zeros((4, 6, 3), dtype=np.uint8)
    face = SimpleNamespace(bbox=np.array([1, 1, 5, 3], dtype=np.float32))
    count = 0

    async def next_frame(websocket, camera, last_sequence):
        nonlocal count
        count += 1
        return backend_main.CameraFrame(count, 0.0, image, 0.0)

    monkeypatch.setattr(backend_main, "next_input_frame", next_frame)
    monkeypatch.setattr(
        backend_main,
        "extract_embedding_from_frame",
        lambda *args: (np.array([1.0, 0.0]), face, "real"),
    )
    led_calls = []
    monkeypatch.setattr(
        backend_main.leds, "registration_active", lambda: led_calls.append("active")
    )
    monkeypatch.setattr(
        backend_main.leds, "registration_done", lambda: led_calls.append("done")
    )
    monkeypatch.setattr(backend_main.leds, "all_off", lambda: led_calls.append("off"))

    asyncio.run(backend_main.websocket_enroll(websocket))

    assert len(websocket.sent) == 30
    assert websocket.sent[-1]["status"] == "Finished"
    assert websocket.sent[-1]["progress"] == 1.0
    assert websocket.sent[-1]["frame_sequence"] == 30
    assert led_calls == ["active", "done"]


def test_enrollment_maps_invalid_frames_and_reactivates_collection_feedback(
    monkeypatch,
):
    websocket = FakeWebSocket()
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    face = SimpleNamespace(bbox=np.array([10, 10, 110, 110], dtype=np.float32))
    frames = 0

    async def next_frame(websocket, camera, last_sequence):
        nonlocal frames
        frames += 1
        if frames > 4:
            raise backend_main.WebSocketDisconnect()
        return backend_main.CameraFrame(frames, 0.0, image, 0.0)

    results = iter(
        [
            (None, face, "spoof"),
            (None, face, "bad_face"),
            (None, None, "no_face"),
            (np.array([1.0, 0.0]), face, "real"),
        ]
    )
    monkeypatch.setattr(backend_main, "next_input_frame", next_frame)
    monkeypatch.setattr(
        backend_main,
        "extract_embedding_from_frame",
        lambda *args: next(results),
    )
    led_calls = []
    monkeypatch.setattr(
        backend_main.leds, "access_denied", lambda: led_calls.append("red")
    )
    monkeypatch.setattr(
        backend_main.leds, "bad_frame", lambda: led_calls.append("yellow")
    )
    monkeypatch.setattr(
        backend_main.leds,
        "registration_active",
        lambda: led_calls.append("active"),
    )
    monkeypatch.setattr(backend_main.leds, "all_off", lambda: led_calls.append("off"))

    asyncio.run(backend_main.websocket_enroll(websocket))

    assert [response["status"] for response in websocket.sent] == [
        "SPOOF DETECTED",
        "Look straight",
        "No face detected",
        "Collecting: 1/30",
    ]
    assert led_calls == ["red", "yellow", "off", "active", "off"]


def test_concurrent_recognition_and_enrollment_are_not_allowed(monkeypatch):
    recognition_socket = FakeWebSocket()
    enrollment_socket = FakeWebSocket()
    recognition_started = asyncio.Event()
    release_recognition = asyncio.Event()

    async def blocked_frame(websocket, camera, last_sequence):
        recognition_started.set()
        await release_recognition.wait()
        raise backend_main.WebSocketDisconnect()

    monkeypatch.setattr(backend_main, "next_input_frame", blocked_frame)
    monkeypatch.setattr(backend_main, "OPERATION_HANDOFF_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(backend_main.leds, "all_off", lambda: None)

    async def scenario():
        recognition = asyncio.create_task(
            backend_main.websocket_recognize(recognition_socket)
        )
        await recognition_started.wait()
        await backend_main.websocket_enroll(enrollment_socket)
        release_recognition.set()
        await recognition

    asyncio.run(scenario())

    assert enrollment_socket.sent[0]["error_code"] == "operation_busy"
    assert enrollment_socket.closed_codes == [1013]
    assert backend_main.operation_lock.locked() is False
