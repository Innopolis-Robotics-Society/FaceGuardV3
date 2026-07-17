import numpy as np
from types import SimpleNamespace

from faceguard.business_logic import process_access_attempt
from faceguard.interfaces import FaceProviderInterface
from faceguard.recognize import InsightFaceProvider


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

    access_granted, status_code, name, score, _ = process_access_attempt(
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

    access_granted, status_code, name, score, _ = process_access_attempt(
        frame=dummy_frame,
        recognizer=recognizer,
        test_db_vector=dummy_db_vector,
    )

    assert access_granted is False
    assert status_code == "no_face"
    assert name == "Unknown"
    assert score == 0.0


def test_qrt_sec_002_production_provider_propagates_liveness_rejection():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    matching_embedding = np.ones(512, dtype=np.float32)
    face = SimpleNamespace(
        bbox=np.array([20, 20, 160, 160], dtype=np.float32),
        det_score=0.99,
        normed_embedding=matching_embedding,
    )
    face_app = SimpleNamespace(get=lambda image: [face])
    liveness_detector = SimpleNamespace(analyze=lambda image, bbox: (False, 0.1))
    recognizer = InsightFaceProvider(face_app, liveness_detector)

    access_granted, status_code, name, score, returned_face = process_access_attempt(
        frame=frame,
        recognizer=recognizer,
        test_db_vector=matching_embedding,
    )

    assert access_granted is False
    assert status_code == "spoof"
    assert name == "Unknown"
    assert score == 0.0
    assert returned_face is face
