import asyncio

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import main as backend_main
from core.security import create_access_token


@pytest.fixture(autouse=True)
def ready_websocket_runtime(monkeypatch):
    monkeypatch.setattr(backend_main, "operation_lock", asyncio.Lock())
    monkeypatch.setattr(
        backend_main,
        "camera_settings",
        backend_main.CameraSettings(source="browser"),
    )
    monkeypatch.setattr(backend_main, "face_app", object())
    monkeypatch.setattr(backend_main, "liveness_detector", object())
    monkeypatch.setattr(backend_main.leds, "all_off", lambda: None)


def test_websocket_boundary_ignores_query_token_and_requires_auth_protocols():
    token = create_access_token({"sub": "operator"})
    client = TestClient(backend_main.app)
    try:
        with pytest.raises(WebSocketDisconnect) as rejected:
            with client.websocket_connect(f"/ws/recognize?token={token}"):
                pass
    finally:
        client.close()

    assert rejected.value.code == 1008


def test_websocket_boundary_rejects_invalid_jwt_with_policy_close():
    client = TestClient(backend_main.app)
    try:
        with client.websocket_connect(
            "/ws/recognize",
            subprotocols=["faceguard.jwt", "bearer.invalid"],
        ) as websocket:
            assert websocket.accepted_subprotocol == "faceguard.jwt"
            with pytest.raises(WebSocketDisconnect) as rejected:
                websocket.receive_json()
    finally:
        client.close()

    assert rejected.value.code == 1008


def test_websocket_boundary_accepts_valid_signed_jwt(monkeypatch):
    async def disconnect_after_accept(websocket, camera, last_sequence):
        raise backend_main.WebSocketDisconnect()

    monkeypatch.setattr(backend_main, "next_input_frame", disconnect_after_accept)
    token = create_access_token({"sub": "operator"})
    client = TestClient(backend_main.app)
    try:
        with client.websocket_connect(
            "/ws/recognize",
            subprotocols=["faceguard.jwt", f"bearer.{token}"],
        ) as websocket:
            assert websocket.accepted_subprotocol == "faceguard.jwt"
    finally:
        client.close()

    assert backend_main.operation_lock.locked() is False
