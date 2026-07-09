import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import numpy as np  # noqa: E402
from faceguard.interfaces import FaceProviderInterface  # noqa: E402
import logging  # noqa: E402
from faceguard.detect import select_closest_face, is_good_face  # noqa: E402

DEFAULT_MODEL_NAME = "buffalo_s"


class LivenessDetector:
    def __init__(self, threshold=0.50):
        import onnxruntime

        self.threshold = threshold
        self.session = onnxruntime.InferenceSession(
            "/root/.insightface/models/minifasnet.onnx",
            providers=["CPUExecutionProvider"],
        )

    def analyze(self, frame: np.ndarray, bbox: np.ndarray) -> tuple[bool, float]:
        import cv2

        # print(f"DEBUG: analyze() запущен. Bbox: {bbox}", flush=True)
        x1, y1, x2, y2 = bbox.astype(int)
        w = x2 - x1
        h = y2 - y1

        cx = x1 + w // 2
        cy = y1 + h // 2

        size = int(max(w, h) * 2.7)

        src_x1 = cx - size // 2
        src_y1 = cy - size // 2
        src_x2 = src_x1 + size
        src_y2 = src_y1 + size

        img_h, img_w = frame.shape[:2]

        crop_x1 = max(0, src_x1)
        crop_y1 = max(0, src_y1)
        crop_x2 = min(img_w, src_x2)
        crop_y2 = min(img_h, src_y2)

        if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
            return False, 0.0

        cropped = frame[crop_y1:crop_y2, crop_x1:crop_x2]

        pad_left = crop_x1 - src_x1
        pad_top = crop_y1 - src_y1
        pad_right = src_x2 - crop_x2
        pad_bottom = src_y2 - crop_y2

        face_crop = cv2.copyMakeBorder(
            cropped,
            pad_top,
            pad_bottom,
            pad_left,
            pad_right,
            borderType=cv2.BORDER_REPLICATE,
        )

        # print(f"DEBUG: Кроп лица успешно сделан. Размер кропа: {face_crop.shape}", flush=True)
        face_crop = cv2.resize(face_crop, (80, 80))
        img = face_crop.astype(np.float32)
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)

        input_name = self.session.get_inputs()[0].name
        raw_outputs = self.session.run(None, {input_name: img})[0][0]

        exp_logits = np.exp(raw_outputs - np.max(raw_outputs))
        probabilities = exp_logits / np.sum(exp_logits)

        mock_liveness_score = float(probabilities[1])
        is_live = mock_liveness_score >= self.threshold
        # print(f"DEBUG: Выход модели MiniFASNet (вероятности): {probabilities}", flush=True)

        return is_live, mock_liveness_score


def create_face_app(model_name: str = DEFAULT_MODEL_NAME):
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(
        name=model_name,
        providers=["CPUExecutionProvider"],
        allowed_modules=["detection", "recognition"],
    )

    app.prepare(ctx_id=-1, det_size=(640, 640))

    return app


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    embedding = np.asarray(embedding, dtype=np.float32)

    norm = np.linalg.norm(embedding)

    if norm == 0:
        return embedding

    return embedding / norm


def get_face_embedding(face) -> np.ndarray:
    embedding = getattr(face, "normed_embedding", None)

    if embedding is None:
        embedding = getattr(face, "embedding", None)

    if embedding is None:
        raise ValueError("Face object does not contain embedding")

    return normalize_embedding(embedding)


def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    # Avg. many face embeddings into one reference embedding
    if len(embeddings) == 0:
        raise ValueError("Cannot average empty embedding list")

    normalized_embeddings = np.array(
        [normalize_embedding(e) for e in embeddings],
        dtype=np.float32,
    )

    mean_embedding = np.mean(normalized_embeddings, axis=0)

    return normalize_embedding(mean_embedding)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = normalize_embedding(a)
    b = normalize_embedding(b)

    return float(np.dot(a, b))


def verify_embedding(
    current_embedding: np.ndarray,
    saved_embedding: np.ndarray,
    threshold: float = 0.50,
):
    score = cosine_similarity(current_embedding, saved_embedding)
    verified = score >= threshold

    return verified, score


def extract_embedding_from_frame(
    app, liveness_detector: LivenessDetector | np.ndarray, frame=None
):
    two_argument_call = frame is None

    if two_argument_call:
        frame = liveness_detector
        liveness_detector = None

    def result(embedding, face, status_code):
        if two_argument_call:
            return embedding, face
        return embedding, face, status_code

    faces = app.get(frame)
    face = select_closest_face(faces)

    if face is None:
        return result(None, None, "no_face")

    if not is_good_face(face, frame):
        return result(None, face, "bad_face")

    if liveness_detector is not None:
        is_live, liveness_score = liveness_detector.analyze(frame, face.bbox)
        if not is_live:
            return result(None, face, "spoof")

    embedding = get_face_embedding(face)

    return result(embedding, face, "real")


def save_embedding(path: str, embedding: np.ndarray):
    directory = os.path.dirname(path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    embedding = normalize_embedding(embedding)

    np.save(path, embedding)


def load_embedding(path: str) -> np.ndarray:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Embedding file not found: {path}")

    embedding = np.load(path)

    return normalize_embedding(embedding)


class InsightFaceProvider(FaceProviderInterface):
    def __init__(self, app, liveness_detector):
        self.app = app
        self.liveness_detector = liveness_detector

    def extract_embedding(self, frame: np.ndarray):
        embedding, face = extract_embedding_from_frame(self.app, frame)
        status_code = "real" if embedding is not None else "no_face"
        return embedding, face, status_code
