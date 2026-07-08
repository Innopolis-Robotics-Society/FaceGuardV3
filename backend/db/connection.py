import streamlit as st
import warnings
from psycopg2 import pool
from contextlib import contextmanager

warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy connectable.*")

@st.cache_resource(show_spinner=False)
def get_pool():
    return pool.SimpleConnectionPool(
        1, 20,
        host=st.secrets["host"],
        database=st.secrets["database"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        sslmode="require",
    )

@contextmanager
def get_db_connection():
    db_pool = get_pool()
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
