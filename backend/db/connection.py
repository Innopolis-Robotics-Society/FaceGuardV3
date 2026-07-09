import warnings
import tomli
from psycopg2 import pool
from contextlib import contextmanager
import os

warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy connectable.*")

# Load secrets from toml
secrets_path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml")
with open(secrets_path, "rb") as f:
    st_secrets = tomli.load(f)

# Use simple caching pattern instead of st.cache_resource
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            1, 20,
            host=st_secrets["host"],
            database=st_secrets["database"],
            user=st_secrets["user"],
            password=st_secrets["password"],
            sslmode="require",
            options="-c timezone=Europe/Moscow"
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
