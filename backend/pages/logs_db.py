import psycopg2 as ps2
import streamlit as st

def get_connection():
    return ps2.connect(
        host=st.secrets["db_host"],
        database=st.secrets["db_name"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"]
    )

def add_log(name: str, status: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO logs (name, status) VALUES (%s, %s)",
                (name, status)
            )
        conn.commit()

def get_all_logs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, time, status FROM logs ORDER BY time DESC")
            rows = cur.fetchall()
    return [
        {"id": r[0], "name": r[1], "time": str(r[2]), "status": r[3]}
        for r in rows
    ]

def delete_old_logs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM logs WHERE time < NOW() - INTERVAL '3 days'"
            )
        conn.commit()