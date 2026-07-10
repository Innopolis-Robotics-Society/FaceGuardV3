import numpy as np

from faceguard.business_logic import process_access_attempt
from faceguard.interfaces import FaceProviderInterface
from tests.mocks import MockFaceRecognizer


def test_qrt_main_003_mock_recognizer_implements_provider_contract():
    recognizer = MockFaceRecognizer(should_fail=False)

    assert isinstance(recognizer, FaceProviderInterface)


def test_qrt_main_003_provider_can_be_swapped_in_access_flow():
    recognizer = MockFaceRecognizer(should_fail=False)
    frame = np.zeros((640, 480, 3), dtype=np.uint8)
    db_vector = np.ones(512, dtype=np.float32)

    access_granted, status_code, name, score = process_access_attempt(
        frame=frame,
        recognizer=recognizer,
        test_db_vector=db_vector,
    )

    assert access_granted is True
    assert status_code == "real"
    assert name == "TestUser"
    assert round(score) == 100


def test_qrt_main_003_provider_failure_returns_application_rejection():
    recognizer = MockFaceRecognizer(should_fail=True)
    frame = np.zeros((640, 480, 3), dtype=np.uint8)
    db_vector = np.ones(512, dtype=np.float32)

    access_granted, status_code, name, score = process_access_attempt(
        frame=frame,
        recognizer=recognizer,
        test_db_vector=db_vector,
    )

    assert access_granted is False
    assert status_code == "no_face"
    assert name == "Unknown"
    assert score == 0.0
