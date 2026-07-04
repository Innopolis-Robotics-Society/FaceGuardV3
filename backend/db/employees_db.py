import psycopg2 as ps2
import psycopg2.extras
import pandas as pd
import streamlit as st
import numpy as np
import sys
import os
from datetime import date, datetime, time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


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
        boundary = time.max if end_of_day else time.min
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


def connect_to_db():
    return ps2.connect(
        host=st.secrets["host"],
        database=st.secrets["database"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        sslmode="require",
    )


def init_db():
    connection = connect_to_db()
    cursor = connection.cursor()
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
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()


def delete_expired_employees():
    connection = connect_to_db()
    cursor = connection.cursor()
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
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()


def load_employees():
    delete_expired_employees()
    connection = connect_to_db()
    query = "SELECT id, name, registration_date, status, start_date, expiration_date FROM employees ORDER BY id;"
    df = pd.read_sql(query, connection)
    connection.close()
    return df


def update_employee(employee_id, name, status, start_date=None, expiration_date=None):
    connection = connect_to_db()
    cursor = connection.cursor()
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
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()


def delete_employee(employee_id):
    connection = connect_to_db()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM employees WHERE id = %s;", (int(employee_id),))
        connection.commit()
    except Exception as e:
        connection.rollback()
        st.error(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()


def add_employees(name, status, embedding=None, start_date=None, expiration_date=None):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
    if cursor.fetchone() is not None:
        st.error("Employee with this name already exists")
        cursor.close()
        connection.close()
        return False

    embedding = embedding.tolist() if embedding is not None else None
    start_date, expiration_date = _normalize_access_window(
        status, start_date, expiration_date
    )

    cursor.execute(
        "INSERT INTO employees (name, status, embedding, start_date, expiration_date) VALUES (%s, %s, %s, %s, %s);",
        (name, status, embedding, start_date, expiration_date),
    )
    connection.commit()
    cursor.close()
    connection.close()
    return True


def get_all_embeddings():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, name, embedding, status, start_date, expiration_date FROM employees WHERE embedding IS NOT NULL"
    )

    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    now = _current_access_time()

    today = date.today()
    embeddings = []
    for row in rows:
        emp_id, name, embedding, status, start_date, expiration_date = row
        if not embedding:
            continue
        if status == "Temporary":
            if not _temporary_access_is_active(start_date, expiration_date, now):
                continue
        embeddings.append((emp_id, name, np.array(embedding)))

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
