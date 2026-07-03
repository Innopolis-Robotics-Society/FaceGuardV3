import psycopg2 as ps2
import psycopg2.extras
import pandas as pd
import streamlit as st
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


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
            AND expiration_date < NOW();
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
        cursor.execute(
            "UPDATE employees SET name = %s, status = %s, start_date = %s, expiration_date = %s WHERE id = %s;",
            (name, status, start_date, expiration_date, int(employee_id))
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

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    embeddings = []
    for row in rows:
        emp_id, name, embedding, status, start_date, expiration_date = row
        if not embedding:
            continue
        if status == "Temporary":
            if start_date and now < start_date:
                continue
            if expiration_date and now > expiration_date:
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
