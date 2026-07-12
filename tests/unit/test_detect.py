import sys
import types
from types import SimpleNamespace

import numpy as np

from faceguard.detect import (
    clamp_bbox,
    crop_face,
    draw_face_box,
    is_good_face,
    select_closest_face,
)


def make_face(bbox, det_score=0.95, embedding=None):
    if embedding is None:
        embedding = np.ones(4, dtype=np.float32)

    return SimpleNamespace(
        bbox=np.array(bbox, dtype=np.float32),
        det_score=det_score,
        embedding=embedding,
    )


def test_select_closest_face_returns_largest_bbox_area():
    small_face = make_face([10, 10, 40, 40])
    large_face = make_face([10, 10, 120, 120])
    medium_face = make_face([10, 10, 80, 80])

    selected = select_closest_face([small_face, large_face, medium_face])

    assert selected is large_face


def test_select_closest_face_returns_none_for_empty_input():
    assert select_closest_face([]) is None
    assert select_closest_face(None) is None


def test_clamp_bbox_limits_coordinates_to_frame_bounds():
    bbox = np.array([-10, 5, 120, 95], dtype=np.float32)

    clamped = clamp_bbox(bbox, frame_shape=(80, 100, 3), padding=10)

    assert clamped == (0, 0, 100, 80)


def test_crop_face_returns_padded_frame_region():
    frame = np.arange(100 * 100 * 3, dtype=np.uint8).reshape((100, 100, 3))
    face = make_face([30, 40, 50, 60])

    crop = crop_face(frame, face, padding=5)

    assert crop.shape == (30, 30, 3)
    np.testing.assert_array_equal(crop, frame[35:65, 25:55])


def test_crop_face_returns_none_for_missing_or_invalid_face():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    assert crop_face(frame, None) is None
    assert crop_face(frame, make_face([50, 50, 50, 60]), padding=0) is None


def test_is_good_face_accepts_valid_face():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    face = make_face([20, 20, 140, 150], det_score=0.99)

    assert is_good_face(face, frame) is True


def test_is_good_face_rejects_invalid_faces():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)

    assert is_good_face(None, frame) is False
    assert is_good_face(make_face([20, 20, 60, 60]), frame) is False
    assert is_good_face(make_face([20, 20, 140, 140], det_score=0.20), frame) is False

    no_embedding_face = SimpleNamespace(
        bbox=np.array([20, 20, 140, 140], dtype=np.float32),
        det_score=0.99,
    )
    assert is_good_face(no_embedding_face, frame) is False


def test_draw_face_box_clamps_coordinates_and_annotates_frame(monkeypatch):
    calls = []
    fake_cv2 = types.ModuleType("cv2")
    fake_cv2.FONT_HERSHEY_SIMPLEX = 4
    fake_cv2.rectangle = lambda *args: calls.append(("rectangle", args))
    fake_cv2.putText = lambda *args: calls.append(("putText", args))
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    frame = np.zeros((100, 120, 3), dtype=np.uint8)
    face = make_face([-10, 5, 140, 90])

    result = draw_face_box(frame, face, "Alice", color=(1, 2, 3))

    assert result is frame
    assert calls[0] == (
        "rectangle",
        (frame, (0, 5), (120, 90), (1, 2, 3), 2),
    )
    assert calls[1] == (
        "putText",
        (frame, "Alice", (0, 30), 4, 0.7, (1, 2, 3), 2),
    )


def test_draw_face_box_leaves_frame_unchanged_without_face(monkeypatch):
    fake_cv2 = types.ModuleType("cv2")
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    assert draw_face_box(frame, None, "ignored") is frame
