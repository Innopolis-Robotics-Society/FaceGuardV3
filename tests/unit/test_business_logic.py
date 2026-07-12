import importlib
import sys
import types

import numpy as np

from faceguard.business_logic import process_access_attempt
from faceguard.interfaces import FaceProviderInterface


class FakeRecognizer(FaceProviderInterface):
    def __init__(self, embedding=None, status_code="real"):
        self.embedding = embedding
        self.status_code = status_code

    def extract_embedding(self, frame: np.ndarray):
        if self.embedding is None:
            return None, None, self.status_code

        return self.embedding, {"source": "fake"}, self.status_code


def test_process_access_attempt_grants_access_for_matching_embeddings():
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    saved_embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    recognizer = FakeRecognizer(
        embedding=np.array([0.95, 0.05, 0.0], dtype=np.float32),
        status_code="real",
    )

    access_granted, status_code, name, score, _ = process_access_attempt(
        frame=frame,
        recognizer=recognizer,
        test_db_vector=saved_embedding,
    )

    assert access_granted is True
    assert status_code == "real"
    assert name == "TestUser"
    assert score > 99.0


def test_process_access_attempt_rejects_non_real_statuses():
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    saved_embedding = np.ones(3, dtype=np.float32)

    for status_code in ("no_face", "spoof", "bad_face"):
        recognizer = FakeRecognizer(
            embedding=np.ones(3, dtype=np.float32),
            status_code=status_code,
        )

        access_granted, returned_status, name, score, _ = process_access_attempt(
            frame=frame,
            recognizer=recognizer,
            test_db_vector=saved_embedding,
        )

        assert access_granted is False
        assert returned_status == status_code
        assert name == "Unknown"
        assert score == 0.0


def test_process_access_attempt_rejects_low_similarity_embeddings():
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    saved_embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    recognizer = FakeRecognizer(
        embedding=np.array([0.0, 1.0, 0.0], dtype=np.float32),
        status_code="real",
    )

    access_granted, status_code, name, score, _ = process_access_attempt(
        frame=frame,
        recognizer=recognizer,
        test_db_vector=saved_embedding,
    )

    assert access_granted is False
    assert status_code == "Access Denied"
    assert name == "Unknown"
    assert score == 0.0


def test_process_access_attempt_uses_database_match(monkeypatch):
    db_package = importlib.import_module("db")
    employees_db = types.ModuleType("db.employees_db")
    received = []
    employees_db.find_closest_embedding = lambda embedding: received.append(
        embedding
    ) or (7, "Alice", 0.876)
    monkeypatch.setitem(sys.modules, "db.employees_db", employees_db)
    monkeypatch.setattr(db_package, "employees_db", employees_db, raising=False)
    embedding = np.array([1.0, 0.0], dtype=np.float32)
    recognizer = FakeRecognizer(embedding=embedding)

    result = process_access_attempt(
        frame=np.zeros((20, 20, 3), dtype=np.uint8), recognizer=recognizer
    )

    assert result[0:4] == (True, "real", "Alice", 87.6)
    assert result[4] == {"source": "fake"}
    assert received == [embedding]


def test_process_access_attempt_denies_when_database_has_no_match(monkeypatch):
    db_package = importlib.import_module("db")
    employees_db = types.ModuleType("db.employees_db")
    employees_db.find_closest_embedding = lambda embedding: None
    monkeypatch.setitem(sys.modules, "db.employees_db", employees_db)
    monkeypatch.setattr(db_package, "employees_db", employees_db, raising=False)
    recognizer = FakeRecognizer(embedding=np.array([1.0, 0.0], dtype=np.float32))

    result = process_access_attempt(
        frame=np.zeros((20, 20, 3), dtype=np.uint8), recognizer=recognizer
    )

    assert result[0:4] == (False, "Access Denied", "Unknown", 0.0)
    assert result[4] == {"source": "fake"}
