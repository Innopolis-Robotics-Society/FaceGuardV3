import pandas as pd
import numpy as np
import sys
import os
import time
from datetime import date, datetime, time as dt_time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.connection import get_db_connection  # noqa: E402

TEMPORARY_ACCESS_DATETIME_MIGRATION = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
        AND table_name = 'employees'
        AND column_name = 'start_date'
        AND data_type = 'date'
    ) THEN
        ALTER TABLE employees
            ALTER COLUMN start_date TYPE TIMESTAMP
            USING start_date::timestamp;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
        AND table_name = 'employees'
        AND column_name = 'expiration_date'
        AND data_type = 'date'
    ) THEN
        ALTER TABLE employees
            ALTER COLUMN expiration_date TYPE TIMESTAMP
            USING expiration_date::timestamp +
                  INTERVAL '1 day' - INTERVAL '1 microsecond';
    END IF;
END $$;
"""

DUPLICATE_SIMILARITY_THRESHOLD = 0.56
DUPLICATE_REGISTRATION_LOCK_ID = 1178682181


class DuplicateEmployeeError(ValueError):
    """Raised when a name or biometric identity is already registered."""


def _as_access_datetime(value, *, end_of_day=False):
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone().replace(tzinfo=None)
        return value

    if isinstance(value, date):
        boundary = dt_time.max if end_of_day else dt_time.min
        return datetime.combine(value, boundary)

    raise TypeError(f"Unsupported temporary access value type: {type(value)!r}")


def _current_access_time():
    return datetime.now().astimezone().replace(tzinfo=None)


def _normalize_access_window(status, start_date=None, expiration_date=None):
    if status != "Temporary":
        return None, None

    return (
        _as_access_datetime(start_date),
        _as_access_datetime(expiration_date, end_of_day=True),
    )


def _temporary_access_is_active(start_date, expiration_date, now=None):
    now = _as_access_datetime(now) if now is not None else _current_access_time()
    start_at = _as_access_datetime(start_date)
    expires_at = _as_access_datetime(expiration_date, end_of_day=True)

    if start_at and now < start_at:
        return False
    if expires_at and now > expires_at:
        return False

    return True


def init_db():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                registration_date DATE DEFAULT CURRENT_DATE,
                status VARCHAR(50) NOT NULL DEFAULT 'Permanent',
                embedding FLOAT8[],
                start_date TIMESTAMP,
                expiration_date TIMESTAMP
            );
            """
            try:
                cursor.execute(create_table_query)
                cursor.execute(TEMPORARY_ACCESS_DATETIME_MIGRATION)
                connection.commit()
            except Exception as e:
                connection.rollback()
                raise RuntimeError("Unable to initialize employees schema") from e


def delete_expired_employees():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    DELETE FROM employees
                    WHERE status = 'Temporary'
                    AND expiration_date IS NOT NULL
                    AND expiration_date < LOCALTIMESTAMP;
                """
                )
                connection.commit()
            except Exception as e:
                connection.rollback()
                raise RuntimeError("Unable to delete expired employees") from e


def load_employees():
    delete_expired_employees()
    with get_db_connection() as connection:
        query = """
        SELECT e.id, e.name, e.registration_date, e.status,
               e.start_date, e.expiration_date,
               (SELECT time FROM logs WHERE name = e.name
                ORDER BY time DESC LIMIT 1) as last_seen
        FROM employees e
        ORDER BY e.id;
        """
        df = pd.read_sql(query, connection)
    return df


def update_employee(employee_id, name, status, start_date=None, expiration_date=None):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            try:
                start_date, expiration_date = _normalize_access_window(
                    status, start_date, expiration_date
                )
                cursor.execute(
                    "UPDATE employees SET name = %s, status = %s, "
                    "start_date = %s, expiration_date = %s WHERE id = %s;",
                    (name, status, start_date, expiration_date, int(employee_id)),
                )
                connection.commit()
                global _embedding_cache
                _embedding_cache = None
            except Exception:
                connection.rollback()
                raise


def delete_employee(employee_id):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "DELETE FROM employees WHERE id = %s;", (int(employee_id),)
                )
                connection.commit()
                global _embedding_cache
                _embedding_cache = None
            except Exception:
                connection.rollback()
                raise


def add_employees(name, status, embedding=None, start_date=None, expiration_date=None):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            try:
                # Serialize the similarity check and INSERT across processes.
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    (DUPLICATE_REGISTRATION_LOCK_ID,),
                )
                if embedding is not None:
                    cursor.execute(
                        "SELECT id, name, embedding, status, start_date, "
                        "expiration_date FROM employees "
                        "WHERE embedding IS NOT NULL"
                    )
                    stored_embeddings = _stored_embeddings(cursor.fetchall())
                    match = _find_closest_in_embeddings(
                        embedding,
                        stored_embeddings,
                        DUPLICATE_SIMILARITY_THRESHOLD,
                    )
                    if match:
                        raise DuplicateEmployeeError(
                            f"Face already registered as {match[1]}"
                        )

                cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
                if cursor.fetchone() is not None:
                    raise DuplicateEmployeeError(
                        "Employee with this name already exists"
                    )

                embedding_list = embedding.tolist() if embedding is not None else None
                start_date, expiration_date = _normalize_access_window(
                    status, start_date, expiration_date
                )
                cursor.execute(
                    "INSERT INTO employees (name, status, embedding, "
                    "start_date, expiration_date) "
                    "VALUES (%s, %s, %s, %s, %s);",
                    (name, status, embedding_list, start_date, expiration_date),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    global _embedding_cache
    _embedding_cache = None
    return True


_embedding_cache = None
_embedding_cache_time = 0


def get_all_embeddings():
    global _embedding_cache, _embedding_cache_time
    now = time.time()
    if _embedding_cache is not None and now - _embedding_cache_time < 60:
        return _embedding_cache

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, embedding, status, start_date, expiration_date "
                "FROM employees WHERE embedding IS NOT NULL"
            )
            rows = cursor.fetchall()

    embeddings = _active_embeddings(rows)

    _embedding_cache = embeddings
    _embedding_cache_time = time.time()
    return embeddings


def _active_embeddings(rows, now=None):
    now_dt = _current_access_time() if now is None else now
    embeddings = []
    for row in rows:
        emp_id, name, embedding, status, start_date, expiration_date = row
        if not embedding:
            continue
        if status == "Temporary" and not _temporary_access_is_active(
            start_date,
            expiration_date,
            now_dt,
        ):
            continue
        embeddings.append((emp_id, name, np.asarray(embedding, dtype=np.float32)))
    return embeddings


def _stored_embeddings(rows):
    """Return every stored identity for duplicate checks, regardless of access."""

    return [
        (emp_id, name, np.asarray(embedding, dtype=np.float32))
        for emp_id, name, embedding, _status, _start, _expiration in rows
        if embedding
    ]


def _find_closest_in_embeddings(target_embedding, embeddings_data, threshold):
    from faceguard.recognize import cosine_similarity

    best_match = None
    best_similarity = 0.0
    for emp_id, name, db_embedding in embeddings_data:
        similarity = cosine_similarity(target_embedding, db_embedding)
        if similarity >= threshold and similarity > best_similarity:
            best_similarity = similarity
            best_match = (emp_id, name, similarity)
    return best_match


def find_closest_embedding(
    target_embedding,
    threshold=DUPLICATE_SIMILARITY_THRESHOLD,
):
    """Find the closest matching embedding in the database"""
    embeddings_data = get_all_embeddings()
    if not embeddings_data:
        return None
    return _find_closest_in_embeddings(
        target_embedding,
        embeddings_data,
        threshold,
    )
