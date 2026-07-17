from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from core import security


def test_access_token_round_trip_preserves_subject_and_has_future_expiration():
    before = datetime.now(timezone.utc)

    token = security.create_access_token({"sub": "operator", "role": "admin"})
    payload = security.verify_token(token)

    assert payload["sub"] == "operator"
    assert payload["role"] == "admin"
    expires_at = datetime.fromtimestamp(payload["exp"], timezone.utc)
    assert expires_at >= before + timedelta(days=6, hours=23)


@pytest.mark.parametrize(
    "token",
    [
        jwt.encode(
            {
                "sub": "operator",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            security.SECRET_KEY,
            algorithm=security.ALGORITHM,
        ),
        jwt.encode(
            {
                "sub": "operator",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            },
            "different-signing-secret-that-is-at-least-32-bytes",
            algorithm=security.ALGORITHM,
        ),
        jwt.encode(
            {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            security.SECRET_KEY,
            algorithm=security.ALGORITHM,
        ),
    ],
)
def test_verify_token_rejects_expired_forged_or_subjectless_tokens(token):
    with pytest.raises(HTTPException) as error:
        security.verify_token(token)

    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_verifies_bearer_credentials():
    token = security.create_access_token({"sub": "operator"})

    payload = security.get_current_user(SimpleNamespace(credentials=token))

    assert payload["sub"] == "operator"
