import sys
from types import SimpleNamespace

import numpy as np
import pytest

import faceguard.main as faceguard_main


class FakeCapture:
    def __init__(self, frames=(), opened=True):
        self.frames = list(frames)
        self.opened = opened
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self):
        self.released = True


def configure_recognition(monkeypatch, capture):
    app = object()
    detector = object()
    saved_embedding = np.array([1.0, 0.0], dtype=np.float32)
    destroyed = []
    monkeypatch.setattr(faceguard_main, "create_face_app", lambda: app)
    monkeypatch.setattr(faceguard_main, "LivenessDetector", lambda: detector)
    monkeypatch.setattr(faceguard_main, "load_embedding", lambda path: saved_embedding)
    monkeypatch.setattr(
        faceguard_main.cv2, "VideoCapture", lambda camera_index: capture
    )
    monkeypatch.setattr(faceguard_main.cv2, "putText", lambda *args, **kwargs: None)
    monkeypatch.setattr(faceguard_main.cv2, "imshow", lambda *args, **kwargs: None)
    monkeypatch.setattr(faceguard_main.cv2, "waitKey", lambda delay: 0)
    monkeypatch.setattr(
        faceguard_main.cv2,
        "destroyAllWindows",
        lambda: destroyed.append(True),
    )
    return app, detector, saved_embedding, destroyed


def test_run_recognition_handles_statuses_and_releases_camera(monkeypatch):
    frame = np.zeros((160, 160, 3), dtype=np.uint8)
    capture = FakeCapture([frame.copy() for _ in range(5)])
    app, detector, saved_embedding, destroyed = configure_recognition(
        monkeypatch, capture
    )
    face = SimpleNamespace(bbox=np.array([10, 10, 130, 130], dtype=np.float32))
    results = iter(
        [
            (np.array([1.0, 0.0]), face, "real"),
            (np.array([0.0, 1.0]), face, "real"),
            (None, face, "spoof"),
            (None, face, "bad_face"),
            (None, None, "no_face"),
        ]
    )
    verify_results = iter([(True, 0.95), (False, 0.1)])
    draw_calls = []

    def fake_extract(received_app, received_detector, received_frame):
        assert received_app is app
        assert received_detector is detector
        return next(results)

    def fake_verify(current_embedding, saved_embedding, threshold):
        assert saved_embedding is configure_saved_embedding
        assert threshold == pytest.approx(0.75)
        return next(verify_results)

    configure_saved_embedding = saved_embedding
    monkeypatch.setattr(faceguard_main, "extract_embedding_from_frame", fake_extract)
    monkeypatch.setattr(faceguard_main, "verify_embedding", fake_verify)
    monkeypatch.setattr(
        faceguard_main,
        "draw_face_box",
        lambda *args, **kwargs: draw_calls.append((args, kwargs)),
    )

    faceguard_main.run_recognition("employee.npy", threshold=0.75, camera_index=2)

    assert capture.released is True
    assert destroyed == [True]
    labels = [call[0][2] for call in draw_calls]
    assert labels == [
        "ACCESS GRANTED | score=0.950",
        "ACCESS DENIED | score=0.100",
        "ACCESS DENIED: SPOOF",
        "Look straight",
    ]
    assert [call[1]["color"] for call in draw_calls] == [
        (0, 255, 0),
        (0, 0, 255),
        (0, 0, 255),
        (0, 255, 255),
    ]


def test_run_recognition_rejects_unavailable_camera(monkeypatch):
    capture = FakeCapture(opened=False)
    configure_recognition(monkeypatch, capture)

    with pytest.raises(RuntimeError, match="Cannot open camera"):
        faceguard_main.run_recognition(camera_index=7)

    assert capture.released is True


def test_run_recognition_releases_camera_after_inference_exception(monkeypatch):
    frame = np.zeros((160, 160, 3), dtype=np.uint8)
    capture = FakeCapture([frame])
    configure_recognition(monkeypatch, capture)
    monkeypatch.setattr(
        faceguard_main,
        "extract_embedding_from_frame",
        lambda *args: (_ for _ in ()).throw(RuntimeError("inference failed")),
    )

    with pytest.raises(RuntimeError, match="inference failed"):
        faceguard_main.run_recognition()

    assert capture.released is True


@pytest.mark.parametrize("mode", ["enroll", "recognize"])
def test_cli_dispatches_selected_mode(monkeypatch, mode):
    enroll_calls = []
    recognize_calls = []
    monkeypatch.setattr(
        faceguard_main, "enroll_user", lambda **kwargs: enroll_calls.append(kwargs)
    )
    monkeypatch.setattr(
        faceguard_main,
        "run_recognition",
        lambda **kwargs: recognize_calls.append(kwargs),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "faceguard",
            mode,
            "--embedding-path",
            "custom.npy",
            "--threshold",
            "0.8",
            "--target-count",
            "15",
            "--camera-index",
            "3",
        ],
    )

    faceguard_main.main()

    if mode == "enroll":
        assert enroll_calls == [
            {
                "embedding_path": "custom.npy",
                "target_count": 15,
                "camera_index": 3,
            }
        ]
        assert recognize_calls == []
    else:
        assert recognize_calls == [
            {
                "embedding_path": "custom.npy",
                "threshold": 0.8,
                "camera_index": 3,
            }
        ]
        assert enroll_calls == []
