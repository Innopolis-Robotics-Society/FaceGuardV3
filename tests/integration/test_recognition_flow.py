import numpy as np

from backend.faceguard.business_logic import process_access_attempt
from backend.faceguard.interfaces import FaceProviderInterface
from backend.faceguard.recognize import normalize_embedding


class FakeRecognitionProvider(FaceProviderInterface):
    def __init__(self, embedding, status_code="real"):
        self.embedding = embedding
        self.status_code = status_code

    def extract_embedding(self, frame: np.ndarray):
        if self.embedding is None:
            return None, None, self.status_code

        return normalize_embedding(self.embedding), {"bbox": [5, 5, 40, 40]}, self.status_code


def test_recognition_flow_grants_access_for_matching_provider_embedding():
    fake_frame = np.zeros((64, 64, 3), dtype=np.uint8)
    database_embedding = normalize_embedding(
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    )
    provider = FakeRecognitionProvider(
        np.array([0.99, 0.01, 0.0, 0.0], dtype=np.float32)
    )

    access_granted, status_code, name, score = process_access_attempt(
        frame=fake_frame,
        recognizer=provider,
        test_db_vector=database_embedding,
    )

    assert access_granted is True
    assert status_code == "real"
    assert name == "TestUser"
    assert score > 99.0


def test_recognition_flow_rejects_low_similarity_provider_embedding():
    fake_frame = np.zeros((64, 64, 3), dtype=np.uint8)
    database_embedding = normalize_embedding(
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    )
    provider = FakeRecognitionProvider(
        np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    )

    access_granted, status_code, name, score = process_access_attempt(
        frame=fake_frame,
        recognizer=provider,
        test_db_vector=database_embedding,
    )

    assert access_granted is False
    assert status_code == "Access Denied"
    assert name == "Unknown"
    assert score == 0.0


def test_recognition_flow_rejects_provider_no_face_status():
    fake_frame = np.zeros((64, 64, 3), dtype=np.uint8)
    database_embedding = normalize_embedding(
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    )
    provider = FakeRecognitionProvider(None, status_code="no_face")

    access_granted, status_code, name, score = process_access_attempt(
        frame=fake_frame,
        recognizer=provider,
        test_db_vector=database_embedding,
    )

    assert access_granted is False
    assert status_code == "no_face"
    assert name == "Unknown"
    assert score == 0.0
