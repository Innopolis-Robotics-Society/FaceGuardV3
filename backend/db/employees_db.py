import pandas as pd
import numpy as np
import sys
import os
import time
from datetime import date, datetime, time as dt_time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db.connection import get_db_connection

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
            USING expiration_date::timestamp + INTERVAL '1 day' - INTERVAL '1 microsecond';
    END IF;
END $$;
"""


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
                print(f"Error: {e}")


def delete_expired_employees():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    DELETE FROM employees
                    WHERE status = 'Temporary'
                    AND expiration_date IS NOT NULL
                    AND expiration_date < LOCALTIMESTAMP;
                """)
                connection.commit()
            except Exception as e:
                connection.rollback()
                print(f"Error: {e}")


def load_employees():
    delete_expired_employees()
    with get_db_connection() as connection:
        query = """
        SELECT e.id, e.name, e.registration_date, e.status, e.start_date, e.expiration_date,
               MAX(l.time) as last_seen
        FROM employees e
        LEFT JOIN logs l ON e.name = l.name AND l.status = 'ACCESS_GRANTED'
        GROUP BY e.id
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
                    "UPDATE employees SET name = %s, status = %s, start_date = %s, expiration_date = %s WHERE id = %s;",
                    (name, status, start_date, expiration_date, int(employee_id)),
                )
                connection.commit()
            except Exception as e:
                connection.rollback()
                print(f"Error: {e}")


def delete_employee(employee_id):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "DELETE FROM employees WHERE id = %s;", (int(employee_id),)
                )
                connection.commit()
            except Exception as e:
                connection.rollback()
                print(f"Error: {e}")


def add_employees(name, status, embedding=None, start_date=None, expiration_date=None):
    if embedding is not None:
        match = find_closest_embedding(embedding)
        if match:
            raise ValueError(f"Face already registered as {match[1]}")

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
            if cursor.fetchone() is not None:
                raise ValueError("Employee with this name already exists")

            embedding_list = embedding.tolist() if embedding is not None else None
            start_date, expiration_date = _normalize_access_window(
                status, start_date, expiration_date
            )

            cursor.execute(
                "INSERT INTO employees (name, status, embedding, start_date, expiration_date) VALUES (%s, %s, %s, %s, %s);",
                (name, status, embedding_list, start_date, expiration_date),
            )
            connection.commit()
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
                "SELECT id, name, embedding, status, start_date, expiration_date FROM employees WHERE embedding IS NOT NULL"
            )
            rows = cursor.fetchall()

    now_dt = _current_access_time()

    embeddings = []
    for row in rows:
        emp_id, name, embedding, status, start_date, expiration_date = row
        if not embedding:
            continue
        if status == "Temporary":
            if not _temporary_access_is_active(start_date, expiration_date, now_dt):
                continue
        embeddings.append((emp_id, name, np.array(embedding)))

    _embedding_cache = embeddings
    _embedding_cache_time = time.time()
    return embeddings


def find_closest_embedding(target_embedding, threshold=0.56):
    """Find the closest matching embedding in the database"""
    from faceguard.recognize import cosine_similarity

    embeddings_data = get_all_embeddings()
    if not embeddings_data:
        return None

    best_match = None
    best_similarity = 0

    for emp_id, name, db_embedding in embeddings_data:
        similarity = cosine_similarity(target_embedding, db_embedding)
        is_match = similarity >= threshold
        if is_match and similarity > best_similarity:
            best_similarity = similarity
            best_match = (emp_id, name, similarity)

    return best_match
