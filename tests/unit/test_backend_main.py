import asyncio
import base64
from datetime import datetime, timedelta, timezone
import importlib
import sys
import types
from types import SimpleNamespace

import jwt
import numpy as np
import pytest


class FakeHTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class FakeWebSocketDisconnect(Exception):
    pass


class FakeFastAPI:
    def __init__(self, **kwargs):
        self.middleware = []
        self.state = SimpleNamespace()
        self.lifespan = kwargs.get("lifespan")

    def add_middleware(self, middleware, **kwargs):
        self.middleware.append((middleware, kwargs))

    def add_exception_handler(self, exc_class, handler):
        pass

    def _decorator(self, *args, **kwargs):
        return lambda function: function

    on_event = _decorator
    get = _decorator
    delete = _decorator
    post = _decorator
    put = _decorator
    websocket = _decorator


class FakeBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.accepted_subprotocol = None
        self.sent = []
        self.headers = {"sec-websocket-protocol": "faceguard.jwt, bearer.fake"}
        self.closed_codes = []

    async def accept(self, subprotocol=None):
        self.accepted = True
        self.accepted_subprotocol = subprotocol

    async def send_json(self, value):
        self.sent.append(value)

    async def close(self, code=None):
        self.closed_codes.append(code)


def module(name, **attributes):
    result = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(result, key, value)
    return result


def load_backend_main(monkeypatch):
    backend_package = importlib.import_module("backend")

    async def default_threadpool(function, *args, **kwargs):
        return function(*args, **kwargs)

    fastapi = module(
        "fastapi",
        FastAPI=FakeFastAPI,
        WebSocket=FakeWebSocket,
        WebSocketDisconnect=FakeWebSocketDisconnect,
        HTTPException=FakeHTTPException,
        Depends=lambda x: None,
        Request=object,
    )
    fastapi.__path__ = []
    middleware = module("fastapi.middleware")
    middleware.__path__ = []
    cors = module("fastapi.middleware.cors", CORSMiddleware=object())
    concurrency = module("fastapi.concurrency", run_in_threadpool=default_threadpool)
    pydantic = module("pydantic", BaseModel=FakeBaseModel)

    employee_calls = []

    class FakeDuplicateEmployeeError(ValueError):
        pass

    employees_db = module(
        "db.employees_db",
        DuplicateEmployeeError=FakeDuplicateEmployeeError,
        add_employees=lambda *args: employee_calls.append(("add", args)),
        delete_employee=lambda *args: employee_calls.append(("delete", args)),
        update_employee=lambda *args: employee_calls.append(("update", args)),
        load_employees=lambda: None,
        init_db=lambda: employee_calls.append(("init", ())),
    )
    log_calls = []
    logs_db = module(
        "db.logs_db",
        get_all_logs=lambda *args: log_calls.append(("get", args)) or [],
        add_log=lambda *args: log_calls.append(("add", args)),
        init_db=lambda: log_calls.append(("init", ())),
        delete_old_logs=lambda: log_calls.append(("cleanup", ())),
    )
    connection_calls = []
    connection = module(
        "db.connection",
        close_pool=lambda: connection_calls.append("close_pool"),
    )
    db = module(
        "db",
        employees_db=employees_db,
        logs_db=logs_db,
        connection=connection,
    )
    db.__path__ = []

    face_app = object()
    liveness_detector = object()

    class FakeLivenessDetector:
        def __new__(cls):
            return liveness_detector

    class FakeInsightFaceProvider:
        def __init__(self, app, detector):
            self.app = app
            self.detector = detector

    recognize = module(
        "faceguard.recognize",
        create_face_app=lambda: face_app,
        LivenessDetector=FakeLivenessDetector,
        InsightFaceProvider=FakeInsightFaceProvider,
        extract_embedding_from_frame=lambda *args: (None, None, "no_face"),
        average_embeddings=lambda embeddings: np.mean(embeddings, axis=0),
    )
    business_logic = module(
        "faceguard.business_logic",
        process_access_attempt=lambda **kwargs: (False, "no_face", "Unknown", 0, None),
    )
    faceguard = module("faceguard", recognize=recognize, business_logic=business_logic)
    faceguard.__path__ = []

    led_calls = []

    def record_led(name):
        return lambda: led_calls.append(name)

    fake_leds = module(
        "leds",
        start_recognizing=record_led("start_recognizing"),
        stop_recognizing=record_led("stop_recognizing"),
        access_granted=record_led("access_granted"),
        access_denied=record_led("access_denied"),
        bad_frame=record_led("bad_frame"),
        registration_active=record_led("registration_active"),
        registration_done=record_led("registration_done"),
        all_off=record_led("all_off"),
        shutdown=record_led("shutdown"),
    )
    fake_cv2 = module(
        "cv2",
        IMREAD_COLOR=1,
        IMWRITE_JPEG_QUALITY=2,
        imdecode=lambda data, mode: np.zeros((2, 2, 3)),
        imencode=lambda extension, image, options: (
            True,
            np.frombuffer(b"jpeg", dtype=np.uint8),
        ),
    )
    bcrypt = module("bcrypt", checkpw=lambda provided, stored: False)
    dotenv = module("dotenv", load_dotenv=lambda: None)

    class FakeLimiter:
        def __init__(self, **kwargs):
            pass

        def limit(self, *args, **kwargs):
            return lambda f: f

    slowapi = module(
        "slowapi", Limiter=FakeLimiter, _rate_limit_exceeded_handler=object()
    )
    slowapi_util = module("slowapi.util", get_remote_address=lambda: "127.0.0.1")
    slowapi_errors = module("slowapi.errors", RateLimitExceeded=Exception)
    slowapi.util = slowapi_util
    slowapi.errors = slowapi_errors

    security = module(
        "core.security",
        create_access_token=lambda d: "fake_token",
        get_current_user=lambda: {"sub": "admin"},
        verify_token=lambda t: {"sub": "admin"},
    )

    replacements = {
        "fastapi": fastapi,
        "fastapi.middleware": middleware,
        "fastapi.middleware.cors": cors,
        "fastapi.concurrency": concurrency,
        "pydantic": pydantic,
        "db": db,
        "db.connection": connection,
        "db.employees_db": employees_db,
        "db.logs_db": logs_db,
        "faceguard": faceguard,
        "faceguard.recognize": recognize,
        "faceguard.business_logic": business_logic,
        "leds": fake_leds,
        "cv2": fake_cv2,
        "bcrypt": bcrypt,
        "dotenv": dotenv,
        "slowapi": slowapi,
        "slowapi.util": slowapi_util,
        "slowapi.errors": slowapi_errors,
        "core.security": security,
    }
    for name, replacement in replacements.items():
        monkeypatch.setitem(sys.modules, name, replacement)
    monkeypatch.setattr(backend_package, "main", None, raising=False)
    monkeypatch.setitem(sys.modules, "backend.main", None)
    del sys.modules["backend.main"]
    backend_main = importlib.import_module("backend.main")
    backend_main.face_app = face_app
    backend_main.liveness_detector = liveness_detector
    dependencies = SimpleNamespace(
        employees_db=employees_db,
        employee_calls=employee_calls,
        logs_db=logs_db,
        log_calls=log_calls,
        recognize=recognize,
        business_logic=business_logic,
        leds=fake_leds,
        led_calls=led_calls,
        cv2=fake_cv2,
        bcrypt=bcrypt,
        face_app=face_app,
        liveness_detector=liveness_detector,
        connection_calls=connection_calls,
        duplicate_error=FakeDuplicateEmployeeError,
    )
    return backend_main, dependencies


def test_startup_initializes_both_database_modules(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)

    async def exercise_lifecycle():
        await backend_main.startup_event()
        await backend_main.shutdown_event()

    asyncio.run(exercise_lifecycle())

    assert dependencies.employee_calls == [("init", ())]
    assert dependencies.log_calls == [("init", ())]


def test_shutdown_releases_led_resources(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)

    asyncio.run(backend_main.shutdown_event())

    assert dependencies.led_calls == ["shutdown"]
    assert dependencies.connection_calls == ["close_pool"]


def test_employee_and_log_endpoints_delegate_to_adapters(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)

    class FakeFrame:
        def __init__(self):
            self.replacements = []

        def replace(self, values):
            self.replacements.append(values)
            return self

        def select_dtypes(self, include):
            assert include == ["datetime64"]
            return SimpleNamespace(columns=[])

        def to_dict(self, orient):
            assert orient == "records"
            return [{"id": 1, "name": "Alice"}]

    frame = FakeFrame()
    monkeypatch.setattr(backend_main, "load_employees", lambda: frame)
    deleted = []
    updated = []
    added = []
    monkeypatch.setattr(
        backend_main, "delete_employee", lambda emp_id: deleted.append(emp_id)
    )
    monkeypatch.setattr(
        backend_main, "update_employee", lambda *args: updated.append(args)
    )
    monkeypatch.setattr(backend_main, "add_employees", lambda *args: added.append(args))
    monkeypatch.setattr(
        backend_main,
        "get_all_logs",
        lambda *args: dependencies.log_calls.append(("get-alias", args)) or ["log"],
    )
    update = backend_main.EmployeeUpdate(name="Alice", status="Permanent")
    addition = backend_main.EmployeeAdd(
        name="Bob", status="Permanent", embedding=[0.25, 0.75]
    )

    assert backend_main.get_employees(user={"sub": "admin"}) == [
        {"id": 1, "name": "Alice"}
    ]
    assert backend_main.delete_emp(3, user={"sub": "admin"}) == {"status": "ok"}
    assert backend_main.update_emp(4, update, user={"sub": "admin"}) == {"status": "ok"}
    assert backend_main.add_emp(addition, user={"sub": "admin"}) == {"status": "ok"}
    assert backend_main.get_logs("2026-07-01", "2026-08-01", user={"sub": "admin"}) == [
        "log"
    ]

    assert frame.replacements[0] == {np.nan: None}
    assert deleted == [3]
    assert updated == [(4, "Alice", "Permanent", None, None)]
    assert added[0][0:2] == ("Bob", "Permanent")
    np.testing.assert_array_equal(added[0][2], np.array([0.25, 0.75]))
    assert added[0][3:] == (None, None)
    assert dependencies.log_calls == [("get-alias", ("2026-07-01", "2026-08-01"))]


def test_employee_endpoints_translate_adapter_errors(monkeypatch):
    backend_main, _ = load_backend_main(monkeypatch)
    update = backend_main.EmployeeUpdate(name="Alice", status="Permanent")
    addition = backend_main.EmployeeAdd(name="Bob", status="Permanent", embedding=[1.0])
    monkeypatch.setattr(
        backend_main,
        "update_employee",
        lambda *args: (_ for _ in ()).throw(RuntimeError("update failed")),
    )

    with pytest.raises(FakeHTTPException) as update_error:
        backend_main.update_emp(1, update, user={"sub": "admin"})

    assert update_error.value.status_code == 400
    assert update_error.value.detail == "update failed"
    monkeypatch.setattr(
        backend_main,
        "add_employees",
        lambda *args: (_ for _ in ()).throw(ValueError("duplicate face")),
    )

    with pytest.raises(FakeHTTPException) as add_error:
        backend_main.add_emp(addition, user={"sub": "admin"})

    assert add_error.value.status_code == 400
    assert add_error.value.detail == "duplicate face"


def test_login_accepts_valid_bcrypt_credentials(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    checked = []
    monkeypatch.setenv("ADMIN_LOGIN", "operator")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "$2b$fake")
    monkeypatch.setattr(
        dependencies.bcrypt,
        "checkpw",
        lambda password, stored: checked.append((password, stored)) or True,
    )

    result = backend_main.login(None, {"username": "operator", "password": "secret"})

    assert result == {"status": "ok", "token": "fake_token"}
    assert checked == [(b"secret", b"$2b$fake")]


@pytest.mark.parametrize(
    "credentials",
    [
        {"username": "wrong", "password": "secret"},
        {"username": "admin", "password": "wrong"},
        {},
    ],
)
def test_login_rejects_invalid_credentials(monkeypatch, credentials):
    backend_main, _ = load_backend_main(monkeypatch)
    monkeypatch.setenv("ADMIN_LOGIN", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "$2b$fake")

    with pytest.raises(FakeHTTPException) as error:
        backend_main.login(None, credentials)

    assert error.value.status_code == 401


def test_drain_websocket_returns_latest_queued_message(monkeypatch):
    backend_main, _ = load_backend_main(monkeypatch)

    class QueuedWebSocket:
        def __init__(self):
            self.messages = ["first", "latest"]

        async def receive_text(self):
            if self.messages:
                return self.messages.pop(0)
            await asyncio.sleep(1)

    result = asyncio.run(backend_main.drain_websocket(QueuedWebSocket()))

    assert result == "latest"


def test_recognition_websocket_grants_access_and_logs(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    encoded = base64.b64encode(b"image").decode("ascii")
    drains = iter([f"data:image/jpeg;base64,{encoded}"])

    async def fake_drain(received_websocket):
        try:
            return next(drains)
        except StopIteration:
            raise FakeWebSocketDisconnect()

    face = SimpleNamespace(bbox=np.array([1, 2, 3, 4]))
    dependencies.business_logic.process_access_attempt = lambda **kwargs: (
        True,
        "real",
        "Alice",
        98.5,
        face,
    )
    monkeypatch.setattr(backend_main, "drain_websocket", fake_drain)
    monkeypatch.setattr(backend_main.time, "time", lambda: 100.0)

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.accepted is True
    assert websocket.sent == [
        {
            "status": "Access Granted",
            "color": "#00FF00",
            "name": "Alice",
            "similarity": "98.5%",
            "box": [1, 2, 3, 4],
            "frame_width": 2,
            "frame_height": 2,
            "frame_sequence": 1,
        }
    ]
    assert dependencies.log_calls == [("add", ("Alice", "ACCESS_GRANTED"))]
    assert dependencies.led_calls == [
        "access_granted",
        "all_off",
    ]


def test_recognition_websocket_requires_two_denied_frames(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    encoded = base64.b64encode(b"image").decode("ascii")
    drains = iter([encoded, encoded])

    async def fake_drain(received_websocket):
        try:
            return next(drains)
        except StopIteration:
            raise FakeWebSocketDisconnect()

    face = SimpleNamespace(bbox=np.array([1, 2, 3, 4]))
    dependencies.business_logic.process_access_attempt = lambda **kwargs: (
        False,
        "Access Denied",
        "Unknown",
        0.0,
        face,
    )
    monkeypatch.setattr(backend_main, "drain_websocket", fake_drain)
    monkeypatch.setattr(backend_main.time, "time", lambda: 100.0)

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert [response["status"] for response in websocket.sent] == [
        "Recognizing...",
        "Access Denied",
    ]
    assert dependencies.log_calls == [("add", ("UNKNOWN", "ACCESS_DENIED"))]
    assert dependencies.led_calls == [
        "start_recognizing",
        "access_denied",
        "all_off",
    ]


def test_recognition_websocket_reports_decode_error(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    drains = iter([base64.b64encode(b"invalid").decode("ascii")])

    async def fake_drain(received_websocket):
        try:
            return next(drains)
        except StopIteration:
            raise FakeWebSocketDisconnect()

    monkeypatch.setattr(backend_main, "drain_websocket", fake_drain)
    monkeypatch.setattr(dependencies.cv2, "imdecode", lambda data, mode: None)

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.sent == [{"status": "Error decoding image"}]
    assert dependencies.log_calls == []
    assert dependencies.led_calls == ["all_off"]


def test_enrollment_websocket_finishes_once_on_thirtieth_embedding(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    encoded = base64.b64encode(b"image").decode("ascii")
    remaining_messages = 30

    async def fake_drain(received_websocket):
        nonlocal remaining_messages
        if remaining_messages == 0:
            raise FakeWebSocketDisconnect()
        remaining_messages -= 1
        return encoded

    face = SimpleNamespace(bbox=np.array([1, 2, 3, 4]))
    embedding = np.array([1.0, 0.0], dtype=np.float32)
    monkeypatch.setattr(backend_main, "drain_websocket", fake_drain)
    monkeypatch.setattr(
        backend_main,
        "extract_embedding_from_frame",
        lambda *args: (embedding, face, "real"),
    )

    asyncio.run(backend_main.websocket_enroll(websocket))

    assert websocket.accepted is True
    assert len(websocket.sent) == 30
    assert websocket.sent[0] == {
        "status": "Collecting: 1/30",
        "color": "#00FF00",
        "box": [1, 2, 3, 4],
        "progress": pytest.approx(1 / 30),
        "frame_width": 2,
        "frame_height": 2,
        "frame_sequence": 1,
    }
    assert websocket.sent[-1] == {
        "status": "Finished",
        "color": "#00FF00",
        "box": [1.0, 2.0, 3.0, 4.0],
        "progress": 1.0,
        "embedding": [1.0, 0.0],
        "frame_width": 2,
        "frame_height": 2,
        "frame_sequence": 30,
    }
    assert dependencies.led_calls.count("registration_active") == 1
    assert dependencies.led_calls.count("registration_done") == 1
    assert dependencies.led_calls[-1] == "registration_done"


class FakeBackendCamera:
    def __init__(self, backend_main, frames=()):
        self.backend_main = backend_main
        self.frames = list(frames)
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def wait_for_frame(self, after_sequence, timeout):
        if not self.frames:
            raise FakeWebSocketDisconnect()
        sequence, image = self.frames.pop(0)
        return self.backend_main.CameraFrame(
            sequence=sequence,
            captured_at=self.backend_main.time.perf_counter(),
            image=image,
            capture_ms=2.5,
        )

    def stop(self):
        self.stopped = True


def test_backend_camera_response_contains_same_frame_preview_dimensions_and_box(
    monkeypatch,
):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    image = np.zeros((4, 6, 3), dtype=np.uint8)
    camera = FakeBackendCamera(backend_main, [(1, image)])
    monkeypatch.setattr(
        backend_main,
        "camera_settings",
        backend_main.CameraSettings(source="backend", index=7),
    )
    monkeypatch.setattr(backend_main, "camera_factory", lambda settings: camera)
    face = SimpleNamespace(bbox=np.array([1, 1, 5, 3], dtype=np.float32))
    dependencies.business_logic.process_access_attempt = lambda **kwargs: (
        True,
        "real",
        "Alice",
        99.0,
        face,
    )

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert camera.started is True
    assert camera.stopped is True
    assert websocket.sent[0] == {
        "status": "Access Granted",
        "color": "#00FF00",
        "name": "Alice",
        "similarity": "99.0%",
        "box": [1.0, 1.0, 5.0, 3.0],
        "frame_width": 6,
        "frame_height": 4,
        "frame_sequence": 1,
        "frame": "data:image/jpeg;base64,anBlZw==",
    }
    assert dependencies.log_calls == [("add", ("Alice", "ACCESS_GRANTED"))]
    assert backend_main.operation_lock.locked() is False


def test_backend_camera_is_released_after_inference_exception(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    image = np.zeros((4, 6, 3), dtype=np.uint8)
    camera = FakeBackendCamera(backend_main, [(1, image)])
    monkeypatch.setattr(
        backend_main,
        "camera_settings",
        backend_main.CameraSettings(source="backend"),
    )
    monkeypatch.setattr(backend_main, "camera_factory", lambda settings: camera)
    dependencies.business_logic.process_access_attempt = lambda **kwargs: (
        _ for _ in ()
    ).throw(RuntimeError("inference failed"))

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert camera.stopped is True
    assert websocket.sent[-1]["fatal"] is True
    assert websocket.sent[-1]["status"] == "Recognition stream error"
    assert websocket.closed_codes == [1011]
    assert backend_main.operation_lock.locked() is False
    assert dependencies.led_calls[-1] == "all_off"


def test_browser_mode_never_constructs_server_camera(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    encoded = base64.b64encode(b"image").decode("ascii")
    drains = iter([encoded])

    async def fake_drain(received_websocket):
        try:
            return next(drains)
        except StopIteration:
            raise FakeWebSocketDisconnect()

    monkeypatch.setattr(backend_main, "drain_websocket", fake_drain)
    monkeypatch.setattr(
        backend_main,
        "camera_factory",
        lambda settings: (_ for _ in ()).throw(
            AssertionError("browser mode must not open VideoCapture")
        ),
    )
    dependencies.business_logic.process_access_attempt = lambda **kwargs: (
        False,
        "no_face",
        "Unknown",
        0.0,
        None,
    )

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.sent[0]["frame_width"] == 2
    assert websocket.sent[0]["frame_height"] == 2
    assert websocket.sent[0]["box"] is None
    assert "frame" not in websocket.sent[0]


def test_operation_lock_rejects_concurrent_enrollment(monkeypatch):
    backend_main, _ = load_backend_main(monkeypatch)
    recognition_socket = FakeWebSocket()
    enrollment_socket = FakeWebSocket()
    recognition_waiting = asyncio.Event()
    allow_disconnect = asyncio.Event()

    async def blocking_drain(received_websocket):
        recognition_waiting.set()
        await allow_disconnect.wait()
        raise FakeWebSocketDisconnect()

    monkeypatch.setattr(backend_main, "drain_websocket", blocking_drain)
    monkeypatch.setattr(backend_main, "OPERATION_HANDOFF_TIMEOUT_SECONDS", 0.01)

    async def scenario():
        recognition_task = asyncio.create_task(
            backend_main.websocket_recognize(recognition_socket)
        )
        await recognition_waiting.wait()
        await backend_main.websocket_enroll(enrollment_socket)
        allow_disconnect.set()
        await recognition_task

    asyncio.run(scenario())

    assert enrollment_socket.accepted is True
    assert enrollment_socket.sent == [
        {
            "status": "Camera is busy with another operation",
            "color": "#FF0000",
            "box": None,
            "fatal": True,
            "error_code": "operation_busy",
        }
    ]
    assert enrollment_socket.closed_codes == [1013]
    assert backend_main.operation_lock.locked() is False


def test_operation_lock_allows_bounded_recognition_to_enrollment_handoff(
    monkeypatch,
):
    backend_main, _ = load_backend_main(monkeypatch)
    recognition_socket = FakeWebSocket()
    enrollment_socket = FakeWebSocket()
    recognition_waiting = asyncio.Event()
    release_recognition = asyncio.Event()
    enrollment_received_lock = asyncio.Event()

    async def handoff_drain(received_websocket):
        if received_websocket is recognition_socket:
            recognition_waiting.set()
            await release_recognition.wait()
            raise FakeWebSocketDisconnect()
        enrollment_received_lock.set()
        raise FakeWebSocketDisconnect()

    monkeypatch.setattr(backend_main, "drain_websocket", handoff_drain)
    monkeypatch.setattr(backend_main, "OPERATION_HANDOFF_TIMEOUT_SECONDS", 0.5)

    async def scenario():
        recognition_task = asyncio.create_task(
            backend_main.websocket_recognize(recognition_socket)
        )
        await recognition_waiting.wait()
        enrollment_task = asyncio.create_task(
            backend_main.websocket_enroll(enrollment_socket)
        )
        await asyncio.sleep(0.01)
        assert enrollment_socket.accepted is False
        release_recognition.set()
        await asyncio.wait_for(enrollment_received_lock.wait(), timeout=0.25)
        await recognition_task
        await enrollment_task

    asyncio.run(scenario())

    assert recognition_socket.accepted is True
    assert enrollment_socket.accepted is True
    assert enrollment_socket.sent == []
    assert enrollment_socket.closed_codes == []
    assert backend_main.operation_lock.locked() is False


def test_websocket_rejects_missing_jwt_before_accept(monkeypatch):
    backend_main, _ = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    websocket.headers = {}

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.accepted is False
    assert websocket.sent == []
    assert websocket.closed_codes == [1008]
    assert backend_main.operation_lock.locked() is False


def test_websocket_rejects_invalid_jwt_with_auth_close_code(monkeypatch):
    backend_main, _ = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    monkeypatch.setattr(
        backend_main,
        "verify_token",
        lambda received: (_ for _ in ()).throw(FakeHTTPException(401, "invalid token")),
    )

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.accepted is True
    assert websocket.accepted_subprotocol == "faceguard.jwt"
    assert websocket.sent == []
    assert websocket.closed_codes == [1008]
    assert backend_main.operation_lock.locked() is False


def test_recognition_websocket_accepts_a_real_signed_jwt(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    secret = "websocket-unit-test-secret-at-least-32-bytes"
    token = jwt.encode(
        {
            "sub": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )
    websocket.headers = {"sec-websocket-protocol": f"faceguard.jwt, bearer.{token}"}
    verified_payloads = []

    def verify_real_token(received_token):
        payload = jwt.decode(received_token, secret, algorithms=["HS256"])
        verified_payloads.append(payload)
        return payload

    async def disconnect_before_first_frame(received_websocket):
        raise FakeWebSocketDisconnect()

    monkeypatch.setattr(backend_main, "verify_token", verify_real_token)
    monkeypatch.setattr(backend_main, "drain_websocket", disconnect_before_first_frame)

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.accepted is True
    assert websocket.accepted_subprotocol == "faceguard.jwt"
    assert verified_payloads[0]["sub"] == "admin"
    assert websocket.closed_codes == []
    assert dependencies.led_calls == ["all_off"]
    assert backend_main.operation_lock.locked() is False


def test_shutdown_stops_active_camera_and_closes_owned_resources(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    stopped = []
    backend_main.app.state.active_camera = SimpleNamespace(
        stop=lambda: stopped.append("camera")
    )

    asyncio.run(backend_main.shutdown_event())

    assert stopped == ["camera"]
    assert backend_main.app.state.active_camera is None
    assert dependencies.led_calls == ["shutdown"]
    assert dependencies.connection_calls == ["close_pool"]


def test_employee_endpoint_maps_duplicate_identity_to_conflict(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    employee = backend_main.EmployeeAdd(
        name="Duplicate",
        status="Permanent",
        embedding=[1.0, 0.0],
    )
    monkeypatch.setattr(
        backend_main,
        "add_employees",
        lambda *args: (_ for _ in ()).throw(
            dependencies.duplicate_error("Face already registered as Alice")
        ),
    )

    with pytest.raises(FakeHTTPException) as error:
        backend_main.add_emp(employee, user={"sub": "admin"})

    assert error.value.status_code == 409
    assert error.value.detail == "Face already registered as Alice"


def test_enrollment_maps_invalid_frames_and_reactivates_collection_feedback(
    monkeypatch,
):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    face = SimpleNamespace(bbox=np.array([10, 10, 110, 110], dtype=np.float32))
    frame_number = 0

    async def next_frame(received_websocket, camera, last_sequence):
        nonlocal frame_number
        frame_number += 1
        if frame_number > 4:
            raise FakeWebSocketDisconnect()
        return backend_main.CameraFrame(
            frame_number,
            backend_main.time.perf_counter(),
            image,
            0.0,
        )

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

    asyncio.run(backend_main.websocket_enroll(websocket))

    assert [response["status"] for response in websocket.sent] == [
        "SPOOF DETECTED",
        "Look straight",
        "No face detected",
        "Collecting: 1/30",
    ]
    assert dependencies.led_calls == [
        "access_denied",
        "bad_frame",
        "all_off",
        "registration_active",
        "all_off",
    ]
