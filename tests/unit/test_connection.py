import importlib
import sys
import types

import pytest


class FakeConnection:
    def __init__(self):
        self.rollback_calls = 0

    def rollback(self):
        self.rollback_calls += 1


class FakePool:
    def __init__(self):
        self.connection = FakeConnection()
        self.returned = []
        self.closeall_calls = 0

    def getconn(self):
        return self.connection

    def putconn(self, connection):
        self.returned.append(connection)

    def closeall(self):
        self.closeall_calls += 1


def load_connection_module(monkeypatch, pool_factory):
    db_package = importlib.import_module("db")
    psycopg2 = types.ModuleType("psycopg2")
    pool_module = types.ModuleType("psycopg2.pool")
    pool_module.ThreadedConnectionPool = pool_factory
    psycopg2.pool = pool_module
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "psycopg2", psycopg2)
    monkeypatch.setitem(sys.modules, "psycopg2.pool", pool_module)
    monkeypatch.setitem(sys.modules, "dotenv", dotenv)
    monkeypatch.setattr(db_package, "connection", None, raising=False)
    monkeypatch.setitem(sys.modules, "db.connection", None)
    del sys.modules["db.connection"]
    return importlib.import_module("db.connection")


def test_get_pool_builds_configured_pool_once(monkeypatch):
    calls = []
    fake_pool = FakePool()

    def pool_factory(min_connections, max_connections, **kwargs):
        calls.append((min_connections, max_connections, kwargs))
        return fake_pool

    monkeypatch.setenv("DB_HOST", "postgres.internal")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "guard")
    monkeypatch.setenv("POSTGRES_USER", "guard-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    connection = load_connection_module(monkeypatch, pool_factory)

    assert connection.get_pool() is fake_pool
    assert connection.get_pool() is fake_pool
    assert calls == [
        (
            1,
            20,
            {
                "host": "postgres.internal",
                "port": 5432,
                "database": "guard",
                "user": "guard-user",
                "password": "secret",
                "options": "-c timezone=Europe/Moscow",
            },
        )
    ]


def test_get_pool_uses_documented_defaults(monkeypatch):
    calls = []

    def pool_factory(*args, **kwargs):
        calls.append(kwargs)
        return FakePool()

    for variable in (
        "DB_HOST",
        "DB_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ):
        monkeypatch.delenv(variable, raising=False)
    connection = load_connection_module(monkeypatch, pool_factory)

    connection.get_pool()

    assert calls == [
        {
            "host": "db",
            "port": 5432,
            "database": "faceguard",
            "user": "postgres",
            "password": "postgres",
            "options": "-c timezone=Europe/Moscow",
        }
    ]


def test_get_db_connection_returns_connection_to_pool_after_success(monkeypatch):
    fake_pool = FakePool()
    connection = load_connection_module(monkeypatch, lambda *args, **kwargs: fake_pool)

    with connection.get_db_connection() as checked_out:
        assert checked_out is fake_pool.connection

    assert fake_pool.returned == [fake_pool.connection]


def test_get_db_connection_returns_connection_to_pool_after_failure(monkeypatch):
    fake_pool = FakePool()
    connection = load_connection_module(monkeypatch, lambda *args, **kwargs: fake_pool)

    with pytest.raises(RuntimeError, match="query failed"):
        with connection.get_db_connection():
            raise RuntimeError("query failed")

    assert fake_pool.returned == [fake_pool.connection]
    assert fake_pool.connection.rollback_calls == 1


def test_close_pool_releases_all_connections_and_allows_reinitialization(monkeypatch):
    pools = [FakePool(), FakePool()]
    connection = load_connection_module(
        monkeypatch, lambda *args, **kwargs: pools.pop(0)
    )

    first_pool = connection.get_pool()
    connection.close_pool()
    second_pool = connection.get_pool()

    assert first_pool.closeall_calls == 1
    assert second_pool is not first_pool
