import numpy as np
from time import perf_counter
from faceguard.business_logic import process_access_attempt
from faceguard.interfaces import FaceProviderInterface
from faceguard.recognize import (
    extract_embedding_from_frame,
    normalize_embedding,
)


class FakeFace:
    def __init__(self):
        self.bbox = np.array([100, 100, 260, 260], dtype=np.float32)
        self.det_score = 0.99
        self.normed_embedding = np.ones(512, dtype=np.float32)


class FakeFaceApp:
    def __init__(self, faces):
        self.faces = faces

    def get(self, frame):
        return self.faces


class FakePipelineRecognizer(FaceProviderInterface):
    """Wraps the real embedding-extraction step behind the FaceProviderInterface
    contract, so the full process_access_attempt pipeline (extract -> compare
    -> decision) can be timed end-to-end, matching the QR-001 scenario."""

    def __init__(self, face_app):
        self.face_app = face_app

    def extract_embedding(self, frame: np.ndarray):
        embedding, face = extract_embedding_from_frame(self.face_app, frame)
        if embedding is None:
            return None, None, "no_face"
        return normalize_embedding(embedding), face, "real"


def test_qrt_perf_001_extracts_embedding_within_three_seconds():
    frame = np.zeros((640, 480, 3), dtype=np.uint8)
    app = FakeFaceApp([FakeFace()])
    started_at = perf_counter()
    embedding, face = extract_embedding_from_frame(app, frame)
    elapsed_seconds = perf_counter() - started_at
    assert embedding is not None
    assert face is not None
    assert embedding.shape == (512,)
    assert elapsed_seconds <= 3.0


def test_qrt_perf_001_returns_decision_shape_when_no_face_found():
    frame = np.zeros((640, 480, 3), dtype=np.uint8)
    app = FakeFaceApp([])
    started_at = perf_counter()
    embedding, face = extract_embedding_from_frame(app, frame)
    elapsed_seconds = perf_counter() - started_at
    assert embedding is None
    assert face is None
    assert elapsed_seconds <= 3.0


def test_qrt_perf_001_full_access_decision_within_three_seconds():
    """End-to-end timing for QR-001: capture -> extract -> compare against the
    database -> access decision. This is the scenario actually described in
    docs/quality-requirements.md (QR-001), not just the extraction substep."""
    frame = np.zeros((640, 480, 3), dtype=np.uint8)
    app = FakeFaceApp([FakeFace()])
    recognizer = FakePipelineRecognizer(app)
    db_vector = normalize_embedding(np.ones(512, dtype=np.float32))

    started_at = perf_counter()
    access_granted, status_code, name, score = process_access_attempt(
        frame=frame,
        recognizer=recognizer,
        test_db_vector=db_vector,
    )
    elapsed_seconds = perf_counter() - started_at

    assert access_granted is True
    assert status_code == "real"
    assert elapsed_seconds <= 3.0
