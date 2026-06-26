import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from faceguard.recognize import extract_embedding_from_frame


class FakeFace:
    def __init__(self):
        self.bbox = np.array([100, 100, 250, 250], dtype=np.float32)
        self.det_score = 0.95
        self.embedding = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self.normed_embedding = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)


class FakeFaceApp:
    def get(self, frame):
        return [FakeFace()]


class FakeLivenessDetector:
    def analyze(self, frame, bbox):
        return True, 0.99


def test_recognition_pipeline_produces_decision_within_three_seconds():
    app = FakeFaceApp()
    liveness_detector = FakeLivenessDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    start = time.perf_counter()

    embedding, face, status = extract_embedding_from_frame(
        app,
        liveness_detector,
        frame,
    )

    elapsed = time.perf_counter() - start

    assert elapsed <= 3.0
    assert embedding is not None
    assert face is not None
    assert status == "real"
    assert np.isclose(np.linalg.norm(embedding), 1.0)