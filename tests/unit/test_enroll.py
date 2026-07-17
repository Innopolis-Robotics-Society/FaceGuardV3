from types import SimpleNamespace

import numpy as np
import pytest

import faceguard.dataset as dataset
import faceguard.enroll as enroll


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


def configure_camera(monkeypatch, capture):
    destroyed = []
    monkeypatch.setattr(enroll.cv2, "VideoCapture", lambda index: capture)
    monkeypatch.setattr(enroll.cv2, "putText", lambda *args, **kwargs: None)
    monkeypatch.setattr(enroll.cv2, "imshow", lambda *args, **kwargs: None)
    monkeypatch.setattr(enroll.cv2, "waitKey", lambda delay: 0)
    monkeypatch.setattr(enroll.cv2, "destroyAllWindows", lambda: destroyed.append(True))
    return destroyed


def configure_models(monkeypatch):
    app = object()
    detector = object()
    monkeypatch.setattr(enroll, "create_face_app", lambda: app)
    monkeypatch.setattr(enroll, "LivenessDetector", lambda: detector)
    return app, detector


def test_enroll_user_collects_and_saves_average_without_camera(monkeypatch, tmp_path):
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    capture = FakeCapture([frame.copy() for _ in range(10)])
    destroyed = configure_camera(monkeypatch, capture)
    app, detector = configure_models(monkeypatch)
    face = SimpleNamespace(bbox=np.array([10, 10, 110, 110], dtype=np.float32))
    draw_calls = []
    saved = {}

    def fake_extract(received_app, received_detector, received_frame):
        assert received_app is app
        assert received_detector is detector
        return np.array([3.0, 4.0], dtype=np.float32), face, "real"

    monkeypatch.setattr(enroll, "extract_embedding_from_frame", fake_extract)
    monkeypatch.setattr(
        enroll,
        "draw_face_box",
        lambda *args, **kwargs: draw_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        enroll,
        "save_embedding",
        lambda path, embedding: saved.update(path=path, embedding=embedding),
    )
    path = tmp_path / "employee.npy"

    enroll.enroll_user(str(path), target_count=10, camera_index=4)

    assert capture.released is True
    assert destroyed == [True]
    assert len(draw_calls) == 10
    assert saved["path"] == str(path)
    np.testing.assert_allclose(
        saved["embedding"], np.array([0.6, 0.8], dtype=np.float32)
    )


def test_enroll_user_releases_camera_before_reporting_insufficient_samples(
    monkeypatch,
):
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    capture = FakeCapture([frame])
    destroyed = configure_camera(monkeypatch, capture)
    configure_models(monkeypatch)
    face = SimpleNamespace(bbox=np.array([10, 10, 110, 110], dtype=np.float32))
    monkeypatch.setattr(
        enroll,
        "extract_embedding_from_frame",
        lambda *args: (np.ones(2, dtype=np.float32), face, "real"),
    )
    monkeypatch.setattr(enroll, "draw_face_box", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="Not enough embeddings collected: 1"):
        enroll.enroll_user(target_count=10)

    assert capture.released is True
    assert destroyed == [True]


def test_enroll_user_rejects_unavailable_camera(monkeypatch):
    capture = FakeCapture(opened=False)
    configure_camera(monkeypatch, capture)
    configure_models(monkeypatch)

    with pytest.raises(RuntimeError, match="Cannot open camera"):
        enroll.enroll_user(camera_index=9)

    assert capture.released is True


def test_enroll_user_releases_camera_after_inference_exception(monkeypatch):
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    capture = FakeCapture([frame])
    destroyed = configure_camera(monkeypatch, capture)
    configure_models(monkeypatch)
    monkeypatch.setattr(
        enroll,
        "extract_embedding_from_frame",
        lambda *args: (_ for _ in ()).throw(RuntimeError("inference failed")),
    )

    with pytest.raises(RuntimeError, match="inference failed"):
        enroll.enroll_user()

    assert capture.released is True
    assert destroyed == [True]


def test_enroll_user_displays_feedback_for_non_real_frames(monkeypatch):
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    capture = FakeCapture([frame.copy() for _ in range(3)])
    configure_camera(monkeypatch, capture)
    configure_models(monkeypatch)
    face = SimpleNamespace(bbox=np.array([10, 10, 110, 110], dtype=np.float32))
    results = iter(
        [
            (None, face, "spoof"),
            (None, face, "bad_face"),
            (None, None, "no_face"),
        ]
    )
    draw_calls = []
    text_calls = []
    monkeypatch.setattr(
        enroll, "extract_embedding_from_frame", lambda *args: next(results)
    )
    monkeypatch.setattr(
        enroll,
        "draw_face_box",
        lambda *args, **kwargs: draw_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        enroll.cv2, "putText", lambda *args, **kwargs: text_calls.append((args, kwargs))
    )

    with pytest.raises(RuntimeError, match="Not enough embeddings collected: 0"):
        enroll.enroll_user(target_count=10)

    labels = [call[0][2] for call in draw_calls]
    assert labels == ["SPOOFING ATTEMPT", "Bad angle/blur"]
    assert any(call[0][1] == "Show your face to the camera" for call in text_calls)


def test_collect_user_face_dataset_delegates_to_enrollment(monkeypatch):
    calls = []
    monkeypatch.setattr(
        dataset,
        "enroll_user",
        lambda **kwargs: calls.append(kwargs) or "collected",
    )

    result = dataset.collect_user_face_dataset("face.npy", 12, 3)

    assert result == "collected"
    assert calls == [
        {
            "embedding_path": "face.npy",
            "target_count": 12,
            "camera_index": 3,
        }
    ]
