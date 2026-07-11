import contextlib
import importlib
import sys
import types
from datetime import datetime


class FakeCursor:
    def __init__(self, rows=(), row=None, error=None):
        self.executed = []
        self.rows = list(rows)
        self.row = row
        self.error = error

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if self.error is not None:
            raise self.error

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeConnection:
    def __init__(self, cursor=None):
        self.cursor_instance = cursor or FakeCursor()
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def load_logs_db(monkeypatch):
    db_package = importlib.import_module("db")
    connection_module = types.ModuleType("db.connection")
    connection_module.get_db_connection = None
    monkeypatch.setitem(sys.modules, "db.connection", connection_module)
    monkeypatch.setattr(db_package, "connection", connection_module, raising=False)
    monkeypatch.setattr(db_package, "logs_db", None, raising=False)
    monkeypatch.setitem(sys.modules, "db.logs_db", None)
    del sys.modules["db.logs_db"]
    return importlib.import_module("db.logs_db")


def use_connection(monkeypatch, logs_db, connection):
    @contextlib.contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(logs_db, "get_db_connection", fake_get_connection)


def test_init_db_creates_table_and_commits(monkeypatch):
    logs_db = load_logs_db(monkeypatch)
    connection = FakeConnection()
    use_connection(monkeypatch, logs_db, connection)

    logs_db.init_db()

    query, params = connection.cursor_instance.executed[0]
    assert "CREATE TABLE IF NOT EXISTS logs" in query
    assert params is None
    assert connection.commits == 1
    assert connection.rollbacks == 0


def test_init_db_rolls_back_database_error(monkeypatch):
    logs_db = load_logs_db(monkeypatch)
    connection = FakeConnection(FakeCursor(error=RuntimeError("database unavailable")))
    use_connection(monkeypatch, logs_db, connection)

    logs_db.init_db()

    assert connection.commits == 0
    assert connection.rollbacks == 1


def test_add_log_uses_deduplication_query_and_parameters(monkeypatch):
    logs_db = load_logs_db(monkeypatch)
    connection = FakeConnection()
    use_connection(monkeypatch, logs_db, connection)

    logs_db.add_log("Alice", "ACCESS_GRANTED")

    query, params = connection.cursor_instance.executed[0]
    assert "WHERE NOT EXISTS" in query
    assert "INTERVAL '1 minute'" in query
    assert params == ("Alice", "ACCESS_GRANTED", "Alice", "ACCESS_GRANTED")
    assert connection.commits == 1


def test_get_all_logs_applies_complete_date_range_and_shapes_rows(monkeypatch):
    logs_db = load_logs_db(monkeypatch)
    timestamp = datetime(2026, 7, 11, 12, 30)
    connection = FakeConnection(
        FakeCursor(rows=[(7, "Alice", timestamp, "ACCESS_GRANTED")])
    )
    use_connection(monkeypatch, logs_db, connection)

    result = logs_db.get_all_logs("2026-07-01", "2026-08-01")

    query, params = connection.cursor_instance.executed[0]
    assert "WHERE time >= %s AND time < %s" in query
    assert query.strip().endswith("ORDER BY time DESC LIMIT 100")
    assert params == ("2026-07-01", "2026-08-01")
    assert result == [
        {
            "id": 7,
            "name": "Alice",
            "time": "2026-07-11 12:30:00",
            "status": "ACCESS_GRANTED",
        }
    ]


def test_get_all_logs_ignores_incomplete_date_range(monkeypatch):
    logs_db = load_logs_db(monkeypatch)
    connection = FakeConnection()
    use_connection(monkeypatch, logs_db, connection)

    assert logs_db.get_all_logs(start_date="2026-07-01") == []

    query, params = connection.cursor_instance.executed[0]
    assert "WHERE" not in query
    assert params == ()


def test_log_maintenance_and_last_entry_queries(monkeypatch):
    logs_db = load_logs_db(monkeypatch)
    timestamp = datetime(2026, 7, 11, 12, 30)
    connection = FakeConnection(FakeCursor(row=(timestamp,)))
    use_connection(monkeypatch, logs_db, connection)

    logs_db.delete_old_logs()
    last_entry = logs_db.get_last_entry("Alice")

    delete_query, delete_params = connection.cursor_instance.executed[0]
    lookup_query, lookup_params = connection.cursor_instance.executed[1]
    assert "INTERVAL '3 days'" in delete_query
    assert delete_params is None
    assert "WHERE name = %s" in lookup_query
    assert lookup_params == ("Alice",)
    assert connection.commits == 1
    assert last_entry == timestamp


def test_last_entry_helpers_handle_empty_and_grouped_results(monkeypatch):
    logs_db = load_logs_db(monkeypatch)
    connection = FakeConnection(FakeCursor(rows=[("Alice", 10), ("Bob", 20)]))
    use_connection(monkeypatch, logs_db, connection)

    assert logs_db.get_last_entry("Missing") is None
    assert logs_db.get_last_entries() == {"Alice": 10, "Bob": 20}

    grouped_query, grouped_params = connection.cursor_instance.executed[1]
    assert "MAX(time)" in grouped_query
    assert grouped_params is None
