import numpy as np
from time import perf_counter

from backend.faceguard.recognize import extract_embedding_from_frame


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
