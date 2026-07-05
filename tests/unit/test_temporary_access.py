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
    def __init__(self):
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
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
