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
        _pool = pool.ThreadedConnectionPool(
            1,
            20,
            host=os.environ.get("DB_HOST", "db"),
            port=int(os.environ.get("DB_PORT", "5432")),
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
    except Exception:
        # Never return a connection left in PostgreSQL's aborted transaction
        # state. Data-access functions may already have rolled back; a second
        # rollback is harmless and keeps this pool boundary safe for callers
        # that do not own explicit transaction cleanup.
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)


def close_pool():
    """Close pooled connections during application/test shutdown."""

    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
