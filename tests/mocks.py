import numpy as np
from faceguard.interfaces import FaceProviderInterface


class MockFaceRecognizer(FaceProviderInterface):
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def extract_embedding(self, frame: np.ndarray):
        if self.should_fail:
            return None, None, "no_face"

        dummy_embedding = np.ones(512, dtype=np.float32)
        return dummy_embedding, {"bbox": [0, 0, 100, 100]}, "real"
