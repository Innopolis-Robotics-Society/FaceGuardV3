import os
import numpy as np
from insightface.app import FaceAnalysis

from .detect import select_closest_face, is_good_face


DEFAULT_MODEL_NAME = "buffalo_l"


def create_face_app(model_name: str = DEFAULT_MODEL_NAME):
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


def extract_embedding_from_frame(app, frame):
    faces = app.get(frame)
    face = select_closest_face(faces)

    if face is None:
        return None, None

    if not is_good_face(face, frame):
        return None, face

    embedding = get_face_embedding(face)

    return embedding, face


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