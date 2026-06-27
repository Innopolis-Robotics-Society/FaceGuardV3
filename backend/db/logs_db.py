import psycopg2 as ps2
import streamlit as st


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
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) NOT NULL
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


def get_connection():
    return ps2.connect(
        host=st.secrets["host"],
        database=st.secrets["database"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        sslmode="require",
    )


def add_log(name: str, status: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO logs (name, status) VALUES (%s, %s)", (name, status)
            )
        conn.commit()


def get_all_logs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, time, status FROM logs ORDER BY time DESC")
            rows = cur.fetchall()
    return [{"id": r[0], "name": r[1], "time": str(r[2]), "status": r[3]} for r in rows]


def delete_old_logs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM logs WHERE time < NOW() - INTERVAL '3 days'")
        conn.commit()
