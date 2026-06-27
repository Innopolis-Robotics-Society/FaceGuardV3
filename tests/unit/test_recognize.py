import numpy as np
import pytest

from backend.faceguard.recognize import (
    average_embeddings,
    cosine_similarity,
    normalize_embedding,
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
