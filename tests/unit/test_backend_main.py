import asyncio
import base64
import importlib
import sys
import types
from types import SimpleNamespace

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
    def __init__(self):
        self.middleware = []
        self.state = SimpleNamespace()

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
        self.sent = []
        self.query_params = {"token": "fake"}

    async def accept(self):
        self.accepted = True

    async def send_json(self, value):
        self.sent.append(value)

    async def close(self, code=None):
        pass


class DisconnectAfterSendWebSocket(FakeWebSocket):
    async def send_json(self, value):
        self.sent.append(value)
        raise FakeWebSocketDisconnect()


class FakeCapture:
    def __init__(self, frame=None, opened=True):
        self.frame = frame
        self.opened = opened
        self.released = False
        self.settings = []

    def isOpened(self):
        return self.opened

    def set(self, prop, value):  # noqa: A003 - mirrors cv2.VideoCapture.set
        self.settings.append((prop, value))
        return True

    def read(self):
        return self.frame is not None, self.frame

    def release(self):
        self.released = True


def module(name, **attributes):
    result = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(result, key, value)
    return result


def load_backend_main(monkeypatch, camera_source=None, camera_index=None):
    if camera_source is None:
        monkeypatch.delenv("CAMERA_SOURCE", raising=False)
    else:
        monkeypatch.setenv("CAMERA_SOURCE", camera_source)
    if camera_index is None:
        monkeypatch.delenv("CAMERA_INDEX", raising=False)
    else:
        monkeypatch.setenv("CAMERA_INDEX", camera_index)
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
    employees_db = module(
        "db.employees_db",
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
    )
    db = module("db", employees_db=employees_db, logs_db=logs_db)
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
    )
    fake_cv2 = module(
        "cv2", IMREAD_COLOR=1, imdecode=lambda data, mode: np.zeros((2, 2, 3))
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
    )
    return backend_main, dependencies


def test_camera_configuration_defaults_to_browser(monkeypatch):
    backend_main, _ = load_backend_main(monkeypatch)

    assert backend_main.CAMERA_SOURCE == "browser"
    assert backend_main.CAMERA_INDEX == 0


def test_camera_configuration_reads_backend_environment(monkeypatch):
    backend_main, _ = load_backend_main(
        monkeypatch, camera_source="backend", camera_index="2"
    )

    assert backend_main.CAMERA_SOURCE == "backend"
    assert backend_main.CAMERA_INDEX == 2


def test_startup_initializes_both_database_modules(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)

    backend_main.startup_event()

    assert dependencies.employee_calls == [("init", ())]
    assert dependencies.log_calls == [("init", ())]


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
    decoded_frames = []

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
    monkeypatch.setattr(backend_main, "CAMERA_SOURCE", "browser")
    monkeypatch.setattr(backend_main, "drain_websocket", fake_drain)
    monkeypatch.setattr(
        dependencies.cv2,
        "imdecode",
        lambda data, mode: decoded_frames.append((data, mode)) or np.zeros((2, 2, 3)),
    )
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
        }
    ]
    assert dependencies.log_calls == [("add", ("Alice", "ACCESS_GRANTED"))]
    assert len(decoded_frames) == 1
    assert dependencies.led_calls == [
        "start_recognizing",
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


def test_backend_camera_open_failure_is_reported_and_released(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    capture = FakeCapture(opened=False)

    monkeypatch.setattr(backend_main, "CAMERA_SOURCE", "backend")
    monkeypatch.setattr(
        dependencies.cv2, "VideoCapture", lambda index: capture, raising=False
    )
    monkeypatch.setattr(dependencies.cv2, "CAP_PROP_BUFFERSIZE", 38, raising=False)

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.sent == [
        {
            "status": "Unable to open backend camera index 0",
            "color": "#FF0000",
            "name": "-",
            "similarity": "-",
        }
    ]
    assert capture.released is True
    assert backend_main.camera_lock.locked() is False


def test_backend_recognition_captures_preview_and_releases_on_disconnect(
    monkeypatch,
):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = DisconnectAfterSendWebSocket()
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    capture = FakeCapture(frame=frame)
    face = SimpleNamespace(bbox=np.array([1, 2, 3, 4]))

    monkeypatch.setattr(backend_main, "CAMERA_SOURCE", "backend")
    monkeypatch.setattr(
        dependencies.cv2, "VideoCapture", lambda index: capture, raising=False
    )
    monkeypatch.setattr(dependencies.cv2, "CAP_PROP_BUFFERSIZE", 38, raising=False)
    monkeypatch.setattr(
        dependencies.cv2,
        "imencode",
        lambda extension, image: (True, np.frombuffer(b"jpeg", dtype=np.uint8)),
        raising=False,
    )
    dependencies.business_logic.process_access_attempt = lambda **kwargs: (
        True,
        "real",
        "Alice",
        91.0,
        face,
    )

    asyncio.run(backend_main.websocket_recognize(websocket))

    assert websocket.sent[0]["frame"] == "data:image/jpeg;base64,anBlZw=="
    assert websocket.sent[0]["status"] == "Access Granted"
    assert capture.settings == [(38, 1)]
    assert capture.released is True
    assert backend_main.camera_lock.locked() is False


def test_backend_camera_releases_after_inference_error(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    capture = FakeCapture(frame=np.zeros((2, 2, 3), dtype=np.uint8))

    monkeypatch.setattr(backend_main, "CAMERA_SOURCE", "backend")
    monkeypatch.setattr(
        dependencies.cv2, "VideoCapture", lambda index: capture, raising=False
    )
    monkeypatch.setattr(
        dependencies.cv2,
        "imencode",
        lambda extension, image: (True, np.frombuffer(b"jpeg", dtype=np.uint8)),
        raising=False,
    )
    monkeypatch.setattr(
        dependencies.business_logic,
        "process_access_attempt",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("inference failed")),
    )

    with pytest.raises(RuntimeError, match="inference failed"):
        asyncio.run(backend_main.websocket_recognize(websocket))

    assert capture.released is True
    assert backend_main.camera_lock.locked() is False


def test_enrollment_websocket_finishes_after_thirty_embeddings(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = FakeWebSocket()
    encoded = base64.b64encode(b"image").decode("ascii")
    remaining_messages = 31

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
    assert len(websocket.sent) == 31
    assert websocket.sent[0] == {
        "status": "Collecting: 1/30",
        "color": "#00FF00",
        "box": [1, 2, 3, 4],
        "progress": pytest.approx(1 / 30),
    }
    assert websocket.sent[-1] == {"status": "Finished", "embedding": [1.0, 0.0]}
    assert dependencies.led_calls.count("registration_active") == 30
    assert dependencies.led_calls[-1] == "all_off"


def test_backend_enrollment_captures_preview_and_releases_on_disconnect(monkeypatch):
    backend_main, dependencies = load_backend_main(monkeypatch)
    websocket = DisconnectAfterSendWebSocket()
    capture = FakeCapture(frame=np.zeros((2, 2, 3), dtype=np.uint8))
    face = SimpleNamespace(bbox=np.array([1, 2, 3, 4]))
    embedding = np.array([1.0, 0.0], dtype=np.float32)

    monkeypatch.setattr(backend_main, "CAMERA_SOURCE", "backend")
    monkeypatch.setattr(
        dependencies.cv2, "VideoCapture", lambda index: capture, raising=False
    )
    monkeypatch.setattr(
        dependencies.cv2,
        "imencode",
        lambda extension, image: (True, np.frombuffer(b"jpeg", dtype=np.uint8)),
        raising=False,
    )
    monkeypatch.setattr(
        backend_main,
        "extract_embedding_from_frame",
        lambda *args: (embedding, face, "real"),
    )

    asyncio.run(backend_main.websocket_enroll(websocket))

    assert websocket.sent == [
        {
            "status": "Collecting: 1/30",
            "color": "#00FF00",
            "box": [1, 2, 3, 4],
            "progress": pytest.approx(1 / 30),
            "frame": "data:image/jpeg;base64,anBlZw==",
        }
    ]
    assert capture.released is True
    assert backend_main.camera_lock.locked() is False
