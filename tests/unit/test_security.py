from datetime import datetime, timedelta, timezone
import importlib
import sys
import types

import jwt
import pytest


def install_fake_dotenv(monkeypatch):
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "dotenv", dotenv)


def install_fake_fastapi(monkeypatch):
    class FakeHTTPException(Exception):
        def __init__(self, status_code, detail, headers=None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
            self.headers = headers

    class FakeHTTPBearer:
        pass

    class FakeCredentials:
        def __init__(self, credentials):
            self.credentials = credentials

    fastapi = types.ModuleType("fastapi")
    fastapi.__path__ = []
    fastapi.HTTPException = FakeHTTPException
    fastapi.Security = lambda dependency: dependency
    fastapi_security = types.ModuleType("fastapi.security")
    fastapi_security.HTTPBearer = FakeHTTPBearer
    fastapi_security.HTTPAuthorizationCredentials = FakeCredentials
    monkeypatch.setitem(sys.modules, "fastapi", fastapi)
    monkeypatch.setitem(sys.modules, "fastapi.security", fastapi_security)


@pytest.fixture
def security(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "unit-test-secret-that-is-not-used-in-production")
    install_fake_dotenv(monkeypatch)
    install_fake_fastapi(monkeypatch)
    sys.modules.pop("core.security", None)
    module = importlib.import_module("core.security")
    yield module
    sys.modules.pop("core.security", None)


def test_real_jwt_round_trip_requires_subject(security):
    token = security.create_access_token({"sub": "admin"})

    payload = security.verify_token(token)

    assert payload["sub"] == "admin"
    assert "exp" in payload


def test_expired_jwt_is_rejected(security):
    token = jwt.encode(
        {
            "sub": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        security.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    with pytest.raises(security.HTTPException) as error:
        security.verify_token(token)

    assert error.value.status_code == 401


def test_jwt_signed_with_another_secret_is_rejected(security):
    token = jwt.encode(
        {
            "sub": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "forged-unit-test-secret-that-is-at-least-32-bytes",
        algorithm=security.ALGORITHM,
    )

    with pytest.raises(security.HTTPException) as error:
        security.verify_token(token)

    assert error.value.status_code == 401


def test_jwt_without_subject_is_rejected(security):
    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        security.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )

    with pytest.raises(security.HTTPException) as error:
        security.verify_token(token)

    assert error.value.status_code == 401


def test_security_configuration_fails_fast_without_jwt_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    install_fake_dotenv(monkeypatch)
    install_fake_fastapi(monkeypatch)
    sys.modules.pop("core.security", None)

    with pytest.raises(RuntimeError, match="JWT_SECRET must be configured"):
        importlib.import_module("core.security")

    sys.modules.pop("core.security", None)
