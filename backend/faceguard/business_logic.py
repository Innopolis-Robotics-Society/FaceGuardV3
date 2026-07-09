import numpy as np
from faceguard.interfaces import FaceProviderInterface
from faceguard.recognize import verify_embedding


def process_access_attempt(
    frame: np.ndarray,
    recognizer: FaceProviderInterface,
    test_db_vector: np.ndarray = None,
):
    embedding, meta, status_code = recognizer.extract_embedding(frame)

    if status_code != "real" or embedding is None:
        return False, status_code, "Unknown", 0.0

    if test_db_vector is not None:
        verified, score = verify_embedding(embedding, test_db_vector)
        if verified:
            return True, "real", "TestUser", score * 100
        return False, "Access Denied", "Unknown", 0.0

    from db.employees_db import find_closest_embedding

    match = find_closest_embedding(embedding)
    if match:
        emp_id, name, similarity = match
        return True, "real", name, similarity * 100

    return False, "Access Denied", "Unknown", 0.0
