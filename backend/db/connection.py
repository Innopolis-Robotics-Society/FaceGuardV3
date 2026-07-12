import warnings
from psycopg2 import pool
from contextlib import contextmanager
import os
from dotenv import load_dotenv

warnings.filterwarnings(
    "ignore", message=".*pandas only supports SQLAlchemy connectable.*"
)

# Load variables from .env if present (e.g., for local script execution)
load_dotenv()

# Use simple caching pattern
_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            1,
            20,
            host=os.environ.get("DB_HOST", "db"),
            database=os.environ.get("POSTGRES_DB", "faceguard"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
            options="-c timezone=Europe/Moscow",
        )
    return _pool


@contextmanager
def get_db_connection():
    db_pool = get_pool()
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
