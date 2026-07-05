import importlib
import sys
import types
from datetime import date, datetime


def load_employees_db(monkeypatch):
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2_extras = types.ModuleType("psycopg2.extras")
    psycopg2.extras = psycopg2_extras
    streamlit = types.SimpleNamespace(secrets={}, error=lambda message: None)
    pandas = types.SimpleNamespace(notna=lambda value: value is not None)
    monkeypatch.setitem(sys.modules, "psycopg2", psycopg2)
    monkeypatch.setitem(sys.modules, "psycopg2.extras", psycopg2_extras)
    monkeypatch.setitem(sys.modules, "streamlit", streamlit)
    monkeypatch.setitem(sys.modules, "pandas", pandas)
    sys.modules.pop("backend.db.employees_db", None)
    return importlib.import_module("backend.db.employees_db")


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
    monkeypatch.setattr(employees_db, "connect_to_db", lambda: connection)
    employees_db.init_db()
    executed_sql = "\n".join(
        query for query, params in connection.cursor_instance.executed
    )
    assert "CREATE TABLE IF NOT EXISTS employees" in executed_sql
    assert "ALTER COLUMN start_date TYPE TIMESTAMP" in executed_sql
    assert "ALTER COLUMN expiration_date TYPE TIMESTAMP" in executed_sql
    assert "expiration_date::timestamp + INTERVAL '1 day'" in executed_sql
    assert "INTERVAL '1 microsecond'" in executed_sql
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True



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
    monkeypatch.setattr(employees_db, "connect_to_db", lambda: connection)

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
    monkeypatch.setattr(employees_db, "connect_to_db", lambda: connection)

    result = employees_db.add_employees("Alice", "Permanent")

    assert result is False
    # Only the duplicate-check SELECT should have run, never an INSERT
    executed_queries = [q for q, _ in connection.cursor_instance.executed]
    assert len(executed_queries) == 1
    assert "SELECT" in executed_queries[0]
    assert connection.committed is False


def test_add_employees_returns_true_and_inserts_on_success(monkeypatch):
    employees_db = load_employees_db(monkeypatch)

    connection = FakeConnection(fetchone_result=None)  # no existing employee
    monkeypatch.setattr(employees_db, "connect_to_db", lambda: connection)

    result = employees_db.add_employees("Bob", "Permanent")

    assert result is True
    executed_queries = [q for q, _ in connection.cursor_instance.executed]
    assert len(executed_queries) == 2  # SELECT check + INSERT
    assert "INSERT INTO employees" in executed_queries[1]
    assert connection.committed is True
