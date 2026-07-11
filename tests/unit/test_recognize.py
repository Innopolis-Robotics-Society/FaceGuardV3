import sys
import types
from types import SimpleNamespace

import numpy as np
import pytest

import faceguard.recognize as recognize
from faceguard.recognize import (
    InsightFaceProvider,
    LivenessDetector,
    average_embeddings,
    cosine_similarity,
    create_face_app,
    extract_embedding_from_frame,
    get_face_embedding,
    load_embedding,
    normalize_embedding,
    save_embedding,
    verify_embedding,
)


def test_normalize_embedding_returns_unit_vector():
    embedding = np.array([3.0, 4.0], dtype=np.float32)

    normalized = normalize_embedding(embedding)

    np.testing.assert_allclose(normalized, np.array([0.6, 0.8], dtype=np.float32))
    assert np.isclose(np.linalg.norm(normalized), 1.0)


def test_normalize_embedding_keeps_zero_vector_unchanged():
    embedding = np.zeros(4, dtype=np.float32)

    normalized = normalize_embedding(embedding)

    np.testing.assert_array_equal(normalized, embedding)
    assert normalized.dtype == np.float32


def test_cosine_similarity_returns_expected_scores():
    assert cosine_similarity(
        np.array([1.0, 0.0], dtype=np.float32),
        np.array([1.0, 0.0], dtype=np.float32),
    ) == pytest.approx(1.0)

    assert cosine_similarity(
        np.array([1.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0], dtype=np.float32),
    ) == pytest.approx(0.0)


def test_cosine_similarity_handles_zero_vector():
    score = cosine_similarity(
        np.zeros(3, dtype=np.float32),
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
    )

    assert score == pytest.approx(0.0)


def test_verify_embedding_accepts_and_rejects_by_threshold():
    saved_embedding = np.array([1.0, 0.0], dtype=np.float32)

    verified, score = verify_embedding(
        np.array([0.8, 0.2], dtype=np.float32),
        saved_embedding,
        threshold=0.90,
    )

    assert verified is True
    assert score == pytest.approx(0.9701425)

    verified, score = verify_embedding(
        np.array([0.2, 0.8], dtype=np.float32),
        saved_embedding,
        threshold=0.90,
    )

    assert verified is False
    assert score == pytest.approx(0.2425356)


def test_average_embeddings_returns_normalized_mean():
    embeddings = [
        np.array([2.0, 0.0], dtype=np.float32),
        np.array([0.0, 2.0], dtype=np.float32),
    ]

    averaged = average_embeddings(embeddings)

    np.testing.assert_allclose(
        averaged,
        np.array([0.70710677, 0.70710677], dtype=np.float32),
        rtol=1e-6,
    )
    assert np.isclose(np.linalg.norm(averaged), 1.0)


def test_average_embeddings_rejects_empty_input():
    with pytest.raises(ValueError, match="Cannot average empty embedding list"):
        average_embeddings([])


def test_get_face_embedding_prefers_normalized_embedding():
    face = SimpleNamespace(
        normed_embedding=np.array([0.0, 2.0], dtype=np.float32),
        embedding=np.array([1.0, 0.0], dtype=np.float32),
    )

    embedding = get_face_embedding(face)

    np.testing.assert_array_equal(embedding, np.array([0.0, 1.0], dtype=np.float32))


def test_get_face_embedding_falls_back_to_raw_embedding():
    face = SimpleNamespace(
        normed_embedding=None,
        embedding=np.array([3.0, 4.0], dtype=np.float32),
    )

    embedding = get_face_embedding(face)

    np.testing.assert_allclose(embedding, np.array([0.6, 0.8], dtype=np.float32))


def test_get_face_embedding_rejects_face_without_embedding():
    with pytest.raises(ValueError, match="does not contain embedding"):
        get_face_embedding(SimpleNamespace())


def test_extract_embedding_reports_detection_and_liveness_failures():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    bad_face = SimpleNamespace(
        bbox=np.array([10, 10, 30, 30], dtype=np.float32),
        det_score=0.99,
        embedding=np.ones(4, dtype=np.float32),
    )
    good_face = SimpleNamespace(
        bbox=np.array([10, 10, 130, 130], dtype=np.float32),
        det_score=0.99,
        embedding=np.ones(4, dtype=np.float32),
    )

    no_face_result = extract_embedding_from_frame(
        SimpleNamespace(get=lambda image: []), SimpleNamespace(), frame
    )
    bad_face_result = extract_embedding_from_frame(
        SimpleNamespace(get=lambda image: [bad_face]), SimpleNamespace(), frame
    )
    spoof_result = extract_embedding_from_frame(
        SimpleNamespace(get=lambda image: [good_face]),
        SimpleNamespace(analyze=lambda image, bbox: (False, 0.1)),
        frame,
    )

    assert no_face_result == (None, None, "no_face")
    assert bad_face_result == (None, bad_face, "bad_face")
    assert spoof_result == (None, good_face, "spoof")


def test_extract_embedding_supports_legacy_two_argument_call():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    face = SimpleNamespace(
        bbox=np.array([10, 10, 130, 130], dtype=np.float32),
        det_score=0.99,
        normed_embedding=np.array([3.0, 4.0], dtype=np.float32),
    )

    embedding, selected_face = extract_embedding_from_frame(
        SimpleNamespace(get=lambda image: [face]), frame
    )

    assert selected_face is face
    np.testing.assert_allclose(embedding, np.array([0.6, 0.8], dtype=np.float32))


def test_create_face_app_configures_cpu_provider(monkeypatch):
    calls = {}

    class FakeFaceAnalysis:
        def __init__(self, **kwargs):
            calls["init"] = kwargs

        def prepare(self, **kwargs):
            calls["prepare"] = kwargs

    insightface = types.ModuleType("insightface")
    insightface.__path__ = []
    insightface_app = types.ModuleType("insightface.app")
    insightface_app.FaceAnalysis = FakeFaceAnalysis
    insightface.app = insightface_app
    monkeypatch.setitem(sys.modules, "insightface", insightface)
    monkeypatch.setitem(sys.modules, "insightface.app", insightface_app)

    app = create_face_app("test-model")

    assert isinstance(app, FakeFaceAnalysis)
    assert calls["init"] == {
        "name": "test-model",
        "providers": ["CPUExecutionProvider"],
        "allowed_modules": ["detection", "recognition"],
    }
    assert calls["prepare"] == {"ctx_id": -1, "det_size": (640, 640)}


def test_liveness_detector_initializes_onnx_session(monkeypatch):
    calls = {}

    class FakeSession:
        def __init__(self, path, providers):
            calls["path"] = path
            calls["providers"] = providers

    onnxruntime = types.ModuleType("onnxruntime")
    onnxruntime.InferenceSession = FakeSession
    monkeypatch.setitem(sys.modules, "onnxruntime", onnxruntime)

    detector = LivenessDetector(threshold=0.7)

    assert isinstance(detector.session, FakeSession)
    assert calls["path"].endswith("/minifasnet.onnx")
    assert calls["providers"] == ["CPUExecutionProvider"]
    assert detector.threshold == pytest.approx(0.7)


def test_liveness_detector_preprocesses_frame_and_applies_threshold(monkeypatch):
    calls = {}

    class FakeSession:
        def get_inputs(self):
            return [SimpleNamespace(name="input")]

        def run(self, outputs, inputs):
            calls["inputs"] = inputs
            return [np.array([[0.0, 2.0]], dtype=np.float32)]

    fake_cv2 = types.ModuleType("cv2")
    fake_cv2.BORDER_REPLICATE = 1

    def copy_make_border(image, top, bottom, left, right, borderType):
        calls["padding"] = (top, bottom, left, right, borderType)
        return np.zeros(
            (image.shape[0] + top + bottom, image.shape[1] + left + right, 3),
            dtype=np.uint8,
        )

    def resize(image, size):
        calls["resize"] = size
        return np.zeros((size[1], size[0], 3), dtype=np.uint8)

    fake_cv2.copyMakeBorder = copy_make_border
    fake_cv2.resize = resize
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    detector = object.__new__(LivenessDetector)
    detector.threshold = 0.85
    detector.session = FakeSession()

    is_live, score = detector.analyze(
        np.zeros((100, 100, 3), dtype=np.uint8),
        np.array([0, 0, 40, 40], dtype=np.float32),
    )

    assert is_live is True
    assert score == pytest.approx(0.880797, rel=1e-5)
    assert calls["padding"] == (34, 0, 34, 0, fake_cv2.BORDER_REPLICATE)
    assert calls["resize"] == (80, 80)
    model_input = calls["inputs"]["input"]
    assert model_input.shape == (1, 3, 80, 80)
    assert model_input.dtype == np.float32


def test_liveness_detector_rejects_bbox_outside_frame():
    detector = object.__new__(LivenessDetector)
    detector.threshold = 0.85
    detector.session = SimpleNamespace()

    result = detector.analyze(
        np.zeros((100, 100, 3), dtype=np.uint8),
        np.array([200, 200, 240, 240], dtype=np.float32),
    )

    assert result == (False, 0.0)


def test_embedding_round_trip_creates_parent_and_normalizes(tmp_path):
    path = tmp_path / "nested" / "embedding.npy"

    save_embedding(str(path), np.array([3.0, 4.0], dtype=np.float32))
    loaded = load_embedding(str(path))

    assert path.exists()
    np.testing.assert_allclose(loaded, np.array([0.6, 0.8], dtype=np.float32))


def test_load_embedding_rejects_missing_file(tmp_path):
    path = tmp_path / "missing.npy"

    with pytest.raises(FileNotFoundError, match="Embedding file not found"):
        load_embedding(str(path))


def test_insightface_provider_delegates_to_extraction(monkeypatch):
    app = object()
    detector = object()
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    expected = (np.ones(2, dtype=np.float32), object(), "real")
    calls = []

    def fake_extract(received_app, received_detector, received_frame):
        calls.append((received_app, received_detector, received_frame))
        return expected

    monkeypatch.setattr(recognize, "extract_embedding_from_frame", fake_extract)

    result = InsightFaceProvider(app, detector).extract_embedding(frame)

    assert result == expected
    assert calls == [(app, detector, frame)]
