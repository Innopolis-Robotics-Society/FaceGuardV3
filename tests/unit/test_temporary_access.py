import contextlib
import importlib
import numpy as np
import pytest
import sys
import types
from datetime import date, datetime


class FakePool:
    def getconn(self):
        return FakeConnection()

    def putconn(self, conn):
        pass


def load_employees_db(monkeypatch):
    db_package = importlib.import_module("db")
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2_extras = types.ModuleType("psycopg2.extras")
    psycopg2.extras = psycopg2_extras
    psycopg2.pool = types.ModuleType("psycopg2.pool")
    psycopg2.pool.SimpleConnectionPool = lambda minconn, maxconn, **kwargs: FakePool()
    streamlit = types.SimpleNamespace(secrets={}, error=lambda message: None)
    pandas = types.SimpleNamespace(notna=lambda value: value is not None)
    tomli = types.ModuleType("tomli")
    tomli.load = lambda f: {}
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "psycopg2", psycopg2)
    monkeypatch.setitem(sys.modules, "psycopg2.extras", psycopg2_extras)
    monkeypatch.setitem(sys.modules, "streamlit", streamlit)
    monkeypatch.setitem(sys.modules, "pandas", pandas)
    monkeypatch.setitem(sys.modules, "tomli", tomli)
    monkeypatch.setitem(sys.modules, "dotenv", dotenv)
    monkeypatch.setattr(db_package, "connection", None, raising=False)
    monkeypatch.setitem(sys.modules, "db.connection", None)
    del sys.modules["db.connection"]
    monkeypatch.setattr(db_package, "employees_db", None, raising=False)
    monkeypatch.setitem(sys.modules, "db.employees_db", None)
    del sys.modules["db.employees_db"]
    return importlib.import_module("db.employees_db")


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.executed = []
        self._fetchone_result = fetchone_result
        self._fetchall_result = fetchall_result or []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self._fetchone_result

    def fetchall(self):
        return self._fetchall_result

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FakeConnection:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.cursor_instance = FakeCursor(fetchone_result, fetchall_result)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# --- Pure helper tests (existing, unchanged) ---


def test_temporary_access_accepts_datetime_window(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    assert employees_db._temporary_access_is_active(
        datetime(2026, 7, 4, 9, 0),
        datetime(2026, 7, 4, 18, 0),
        now=datetime(2026, 7, 4, 12, 0),
    )


def test_temporary_access_rejects_before_start(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    assert not employees_db._temporary_access_is_active(
        datetime(2026, 7, 4, 9, 0),
        datetime(2026, 7, 4, 18, 0),
        now=datetime(2026, 7, 4, 8, 59),
    )


def test_temporary_access_rejects_after_expiration(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    assert not employees_db._temporary_access_is_active(
        datetime(2026, 7, 4, 9, 0),
        datetime(2026, 7, 4, 18, 0),
        now=datetime(2026, 7, 4, 18, 1),
    )


def test_temporary_access_handles_legacy_date_values(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    assert employees_db._temporary_access_is_active(
        date(2026, 7, 4),
        date(2026, 7, 4),
        now=datetime(2026, 7, 4, 23, 59, 59),
    )
    assert not employees_db._temporary_access_is_active(
        date(2026, 7, 4),
        date(2026, 7, 4),
        now=datetime(2026, 7, 5, 0, 0),
    )


def test_temporary_access_normalizes_dates_before_database_write(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    start_at, expires_at = employees_db._normalize_access_window(
        "Temporary",
        date(2026, 7, 4),
        date(2026, 7, 5),
    )
    assert start_at == datetime(2026, 7, 4, 0, 0)
    assert expires_at == datetime(2026, 7, 5, 23, 59, 59, 999999)


def test_init_db_runs_date_to_timestamp_migration(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    connection = FakeConnection()

    @contextlib.contextmanager
    def mock_get_conn():
        yield connection

    monkeypatch.setattr(employees_db, "get_db_connection", mock_get_conn)
    employees_db.init_db()
    executed_sql = "\n".join(
        query for query, params in connection.cursor_instance.executed
    )
    assert "CREATE TABLE IF NOT EXISTS employees" in executed_sql
    assert "ALTER COLUMN start_date TYPE TIMESTAMP" in executed_sql
    assert "ALTER COLUMN expiration_date TYPE TIMESTAMP" in executed_sql
    assert "expiration_date::timestamp +" in executed_sql
    assert "INTERVAL '1 day'" in executed_sql
    assert "INTERVAL '1 microsecond'" in executed_sql
    assert connection.committed is True
    assert connection.rolled_back is False


# --- New: tests on the actual public functions, not just the helpers ---


def test_get_all_embeddings_excludes_expired_and_not_yet_started(monkeypatch):
    """Regression test for bug 1 (expired access still granted) and bug 3
    (access before start_date not blocked). Verifies get_all_embeddings()
    itself calls _temporary_access_is_active() correctly, not just that the
    helper works in isolation."""
    employees_db = load_employees_db(monkeypatch)

    now = datetime(2026, 7, 4, 12, 0)
    monkeypatch.setattr(employees_db, "_current_access_time", lambda: now)

    rows = [
        # Permanent — always included
        (1, "Permanent Alice", [0.1, 0.2], "Permanent", None, None),
        # Temporary, expired — must be excluded (bug 1)
        (
            2,
            "Expired Bob",
            [0.3, 0.4],
            "Temporary",
            datetime(2026, 7, 1, 0, 0),
            datetime(2026, 7, 3, 23, 59, 59),
        ),
        # Temporary, not started yet — must be excluded (bug 3)
        (
            3,
            "Future Dave",
            [0.5, 0.6],
            "Temporary",
            datetime(2026, 7, 5, 0, 0),
            datetime(2026, 7, 10, 23, 59, 59),
        ),
        # Temporary, currently active — must be included
        (
            4,
            "Active Carol",
            [0.7, 0.8],
            "Temporary",
            datetime(2026, 7, 4, 9, 0),
            datetime(2026, 7, 4, 18, 0),
        ),
    ]
    connection = FakeConnection(fetchall_result=rows)
    monkeypatch.setattr(employees_db, "get_db_connection", lambda: connection)

    result = employees_db.get_all_embeddings()
    names = [name for _, name, _ in result]

    assert "Permanent Alice" in names
    assert "Active Carol" in names
    assert "Expired Bob" not in names
    assert "Future Dave" not in names
    assert len(result) == 2


def test_add_employees_returns_false_and_skips_insert_on_duplicate(monkeypatch):
    """Regression test for bug 2 (add_employees silently succeeded in the
    UI even on a duplicate name because it returned nothing)."""
    employees_db = load_employees_db(monkeypatch)

    connection = FakeConnection(fetchone_result=(1,))  # existing employee found

    @contextlib.contextmanager
    def mock_get_conn():
        yield connection

    monkeypatch.setattr(employees_db, "get_db_connection", mock_get_conn)

    with pytest.raises(ValueError, match="Employee with this name already exists"):
        employees_db.add_employees("Alice", "Permanent")
    # Only the duplicate-check SELECT should have run, never an INSERT
    executed_queries = [q for q, _ in connection.cursor_instance.executed]
    assert len(executed_queries) == 1
    assert "SELECT" in executed_queries[0]
    assert connection.committed is False


def test_add_employees_returns_true_and_inserts_on_success(monkeypatch):
    employees_db = load_employees_db(monkeypatch)

    connection = FakeConnection(fetchone_result=None)  # no existing employee

    @contextlib.contextmanager
    def mock_get_conn():
        yield connection

    monkeypatch.setattr(employees_db, "get_db_connection", mock_get_conn)

    result = employees_db.add_employees("Bob", "Permanent")

    assert result is True
    executed_queries = [q for q, _ in connection.cursor_instance.executed]
    assert len(executed_queries) == 2  # SELECT check + INSERT
    assert "INSERT INTO employees" in executed_queries[1]
    assert connection.committed is True


def test_access_datetime_rejects_unsupported_values(monkeypatch):
    employees_db = load_employees_db(monkeypatch)

    with pytest.raises(TypeError, match="Unsupported temporary access value type"):
        employees_db._as_access_datetime("2026-07-11")


def test_permanent_access_discards_temporary_window(monkeypatch):
    employees_db = load_employees_db(monkeypatch)

    assert employees_db._normalize_access_window(
        "Permanent", date(2026, 7, 1), date(2026, 7, 2)
    ) == (None, None)


def test_update_employee_normalizes_window_commits_and_invalidates_cache(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    connection = FakeConnection()

    @contextlib.contextmanager
    def mock_get_conn():
        yield connection

    monkeypatch.setattr(employees_db, "get_db_connection", mock_get_conn)
    employees_db._embedding_cache = ["cached"]

    employees_db.update_employee(
        "7",
        "Alice",
        "Temporary",
        date(2026, 7, 11),
        date(2026, 7, 12),
    )

    query, params = connection.cursor_instance.executed[0]
    assert query.startswith("UPDATE employees")
    assert params == (
        "Alice",
        "Temporary",
        datetime(2026, 7, 11, 0, 0),
        datetime(2026, 7, 12, 23, 59, 59, 999999),
        7,
    )
    assert connection.committed is True
    assert employees_db._embedding_cache is None


def test_update_employee_rolls_back_query_failure(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    connection = FakeConnection()
    connection.cursor_instance.execute = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("write failed")
    )

    @contextlib.contextmanager
    def mock_get_conn():
        yield connection

    monkeypatch.setattr(employees_db, "get_db_connection", mock_get_conn)

    employees_db.update_employee(1, "Alice", "Permanent")

    assert connection.committed is False
    assert connection.rolled_back is True


def test_delete_employee_uses_integer_id_and_invalidates_cache(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    connection = FakeConnection()

    @contextlib.contextmanager
    def mock_get_conn():
        yield connection

    monkeypatch.setattr(employees_db, "get_db_connection", mock_get_conn)
    employees_db._embedding_cache = ["cached"]

    employees_db.delete_employee("12")

    query, params = connection.cursor_instance.executed[0]
    assert query.startswith("DELETE FROM employees")
    assert params == (12,)
    assert connection.committed is True
    assert employees_db._embedding_cache is None


def test_add_employees_rejects_duplicate_embedding_before_query(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    monkeypatch.setattr(
        employees_db,
        "find_closest_embedding",
        lambda embedding: (4, "Existing Alice", 0.99),
    )
    monkeypatch.setattr(
        employees_db,
        "get_db_connection",
        lambda: pytest.fail("database should not be accessed"),
    )

    with pytest.raises(ValueError, match="Face already registered as Existing Alice"):
        employees_db.add_employees(
            "New Alice", "Permanent", embedding=np.array([1.0, 0.0])
        )


def test_add_employees_serializes_embedding_and_temporary_dates(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    connection = FakeConnection(fetchone_result=None)

    @contextlib.contextmanager
    def mock_get_conn():
        yield connection

    monkeypatch.setattr(employees_db, "get_db_connection", mock_get_conn)
    monkeypatch.setattr(employees_db, "find_closest_embedding", lambda embedding: None)

    result = employees_db.add_employees(
        "Carol",
        "Temporary",
        embedding=np.array([0.25, 0.75]),
        start_date=date(2026, 7, 11),
        expiration_date=date(2026, 7, 12),
    )

    insert_query, params = connection.cursor_instance.executed[1]
    assert "INSERT INTO employees" in insert_query
    assert params == (
        "Carol",
        "Temporary",
        [0.25, 0.75],
        datetime(2026, 7, 11, 0, 0),
        datetime(2026, 7, 12, 23, 59, 59, 999999),
    )
    assert result is True
    assert connection.committed is True


def test_get_all_embeddings_returns_fresh_cache_without_query(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    cached = [(1, "Alice", np.array([1.0, 0.0]))]
    employees_db._embedding_cache = cached
    employees_db._embedding_cache_time = 100.0
    monkeypatch.setattr(employees_db.time, "time", lambda: 120.0)
    monkeypatch.setattr(
        employees_db,
        "get_db_connection",
        lambda: pytest.fail("fresh cache should avoid a database query"),
    )

    assert employees_db.get_all_embeddings() is cached


def test_find_closest_embedding_returns_best_match_above_threshold(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    monkeypatch.setattr(
        employees_db,
        "get_all_embeddings",
        lambda: [
            (1, "Weak", np.array([0.8, 0.2], dtype=np.float32)),
            (2, "Best", np.array([1.0, 0.0], dtype=np.float32)),
            (3, "Rejected", np.array([0.0, 1.0], dtype=np.float32)),
        ],
    )

    match = employees_db.find_closest_embedding(
        np.array([1.0, 0.0], dtype=np.float32), threshold=0.9
    )

    assert match[0:2] == (2, "Best")
    assert match[2] == pytest.approx(1.0)


def test_find_closest_embedding_handles_empty_database(monkeypatch):
    employees_db = load_employees_db(monkeypatch)
    monkeypatch.setattr(employees_db, "get_all_embeddings", lambda: [])

    assert employees_db.find_closest_embedding(np.ones(2)) is None
