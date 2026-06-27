import numpy as np

from backend.faceguard.business_logic import process_access_attempt
from backend.faceguard.interfaces import FaceProviderInterface


class FakeSpoofRecognizer(FaceProviderInterface):
    def __init__(self, embedding=None, status_code="real"):
        self.embedding = embedding
        self.status_code = status_code

    def extract_embedding(self, frame: np.ndarray):
        if self.embedding is None:
            return None, None, self.status_code

        return self.embedding, {"bbox": [0, 0, 100, 100]}, self.status_code


def test_qrt_sec_002_rejects_spoof_status_before_matching():
    dummy_frame = np.zeros((640, 480, 3), dtype=np.uint8)
    dummy_embedding = np.ones(512, dtype=np.float32)
    dummy_db_vector = np.ones(512, dtype=np.float32)

    recognizer = FakeSpoofRecognizer(
        embedding=dummy_embedding,
        status_code="spoof",
    )

    access_granted, status_code, name, score = process_access_attempt(
        frame=dummy_frame,
        recognizer=recognizer,
        test_db_vector=dummy_db_vector,
    )

    assert access_granted is False
    assert status_code == "spoof"
    assert name == "Unknown"
    assert score == 0.0


def test_qrt_sec_002_rejects_no_face_input():
    dummy_frame = np.zeros((640, 480, 3), dtype=np.uint8)
    dummy_db_vector = np.ones(512, dtype=np.float32)

    recognizer = FakeSpoofRecognizer(
        embedding=None,
        status_code="no_face",
    )

    access_granted, status_code, name, score = process_access_attempt(
        frame=dummy_frame,
        recognizer=recognizer,
        test_db_vector=dummy_db_vector,
    )

    assert access_granted is False
    assert status_code == "no_face"
    assert name == "Unknown"
    assert score == 0.0


def test_qrt_sec_002_rejects_at_least_9_out_of_10_low_similarity_attempts():
    dummy_frame = np.zeros((640, 480, 3), dtype=np.uint8)
    dummy_db_vector = np.ones(512, dtype=np.float32)

    rejected = 0

    for index in range(10):
        spoof_embedding = np.zeros(512, dtype=np.float32)
        spoof_embedding[index] = 1.0

        recognizer = FakeSpoofRecognizer(
            embedding=spoof_embedding,
            status_code="real",
        )

        access_granted, status_code, name, score = process_access_attempt(
            frame=dummy_frame,
            recognizer=recognizer,
            test_db_vector=dummy_db_vector,
        )

        if access_granted is False:
            rejected += 1

        assert status_code == "Access Denied"
        assert name == "Unknown"
        assert score == 0.0

    assert rejected >= 9
