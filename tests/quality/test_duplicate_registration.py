"""QRT-005: duplicate registration through FastAPI and real PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_INTEGRATION") != "1",
    reason="requires the isolated FaceGuard PostgreSQL test service",
)


@pytest.fixture()
def postgres_database():
    database = os.environ.get("POSTGRES_DB", "")
    if database != "faceguard_test":
        pytest.fail("QRT-005 refuses to run unless POSTGRES_DB=faceguard_test")

    from db.connection import close_pool, get_db_connection
    from db.employees_db import init_db

    close_pool()
    init_db()
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE employees RESTART IDENTITY")
        connection.commit()
    try:
        yield get_db_connection
    finally:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE employees RESTART IDENTITY")
            connection.commit()
        close_pool()


@pytest.fixture()
def authenticated_client(postgres_database):
    from fastapi.testclient import TestClient

    from core.security import create_access_token
    from main import app

    token = create_access_token({"sub": "qrt-operator"})
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
    client.close()


def employee_rows(get_connection):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name, status, embedding, start_date, expiration_date "
                "FROM employees ORDER BY id"
            )
            return cursor.fetchall()


def registration(name, embedding):
    return {
        "name": name,
        "status": "Permanent",
        "embedding": embedding,
        "start_date": None,
        "expiration_date": None,
    }


def test_qrt_005_rejects_same_face_without_mutating_existing_employee(
    authenticated_client,
    postgres_database,
):
    original = registration("Existing Alice", [1.0, 0.0, 0.0])

    initial_response = authenticated_client.post("/api/employees", json=original)
    rows_after_initial_registration = employee_rows(postgres_database)
    duplicate_response = authenticated_client.post(
        "/api/employees",
        json=registration("Duplicate Alice", [0.9999, 0.01, 0.0]),
    )
    rows_after_duplicate_attempt = employee_rows(postgres_database)

    assert initial_response.status_code == 200
    assert initial_response.json() == {"status": "ok"}
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "Face already registered as Existing Alice"
    }
    assert len(rows_after_initial_registration) == 1
    assert rows_after_duplicate_attempt == rows_after_initial_registration
    assert rows_after_duplicate_attempt[0][0:2] == (
        "Existing Alice",
        "Permanent",
    )

    # Cosine similarity with the existing [1, 0, 0] vector is 0.55: close
    # to, but below, the production duplicate threshold of 0.56.
    distinct_response = authenticated_client.post(
        "/api/employees",
        json=registration("Similar but distinct Bob", [0.55, 0.83516465, 0.0]),
    )
    rows_after_distinct_registration = employee_rows(postgres_database)

    assert distinct_response.status_code == 200
    assert distinct_response.json() == {"status": "ok"}
    assert [row[0] for row in rows_after_distinct_registration] == [
        "Existing Alice",
        "Similar but distinct Bob",
    ]


def test_qrt_005_serializes_concurrent_similarity_check_and_insert(
    postgres_database,
):
    from fastapi.testclient import TestClient

    from core.security import create_access_token
    from main import app

    headers = {
        "Authorization": f"Bearer {create_access_token({'sub': 'qrt-operator'})}"
    }

    def submit(name):
        client = TestClient(app, headers=headers)
        try:
            return client.post(
                "/api/employees",
                json=registration(name, [0.2, 0.8, 0.1]),
            )
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(submit, ("Concurrent Alice", "Concurrent Bob")))

    assert sorted(response.status_code for response in responses) == [200, 409]
    rows = employee_rows(postgres_database)
    assert len(rows) == 1
    assert rows[0][0] in {"Concurrent Alice", "Concurrent Bob"}
