"""Tests for embedding generation and cosine similarity."""

from unittest.mock import MagicMock, patch

import numpy as np

from app.services.embedding import cosine_similarity, generate_embeddings


def _make_mock_model():
    """Create a mock SentenceTransformer that returns 768-dim vectors."""
    model = MagicMock()

    def mock_encode(texts, **kwargs):
        result = []
        for text in texts:
            rng = np.random.RandomState(hash(text) % (2**31))
            vec = rng.randn(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            result.append(vec)
        return np.array(result)

    model.encode = mock_encode
    return model


# ---------------------------------------------------------------------------
# Embedding dimension tests
# ---------------------------------------------------------------------------


@patch("app.services.embedding.load_embedding_model")
def test_embedding_dimension(mock_load):
    """Generated embedding has 768 dimensions."""
    mock_load.return_value = _make_mock_model()

    embeddings = generate_embeddings(["Sample text for embedding test"])

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 768


@patch("app.services.embedding.load_embedding_model")
def test_batch_embedding(mock_load):
    """Batch embedding returns correct count and dimensions."""
    mock_load.return_value = _make_mock_model()

    texts = ["First sentence", "Second sentence", "Third sentence"]
    embeddings = generate_embeddings(texts)

    assert len(embeddings) == 3
    for emb in embeddings:
        assert len(emb) == 768
        assert all(isinstance(v, float) for v in emb)


@patch("app.services.embedding.load_embedding_model")
def test_embedding_empty_list(mock_load):
    """generate_embeddings returns empty list for empty input."""
    result = generate_embeddings([])
    assert result == []
    mock_load.assert_not_called()


# ---------------------------------------------------------------------------
# Cosine similarity tests
# ---------------------------------------------------------------------------


def test_cosine_similarity_identical():
    """Cosine similarity of identical vectors is ~1.0."""
    vec = np.random.randn(768).tolist()
    sim = cosine_similarity(vec, vec)
    assert abs(sim - 1.0) < 1e-6


def test_cosine_similarity_orthogonal():
    """Cosine similarity of orthogonal vectors is ~0.0."""
    vec_a = [0.0] * 768
    vec_a[0] = 1.0
    vec_b = [0.0] * 768
    vec_b[1] = 1.0
    sim = cosine_similarity(vec_a, vec_b)
    assert abs(sim) < 1e-6


def test_cosine_similarity_opposite():
    """Cosine similarity of opposite vectors is ~-1.0."""
    vec_a = np.random.randn(768).tolist()
    vec_b = [-v for v in vec_a]
    sim = cosine_similarity(vec_a, vec_b)
    assert abs(sim - (-1.0)) < 1e-6


def test_cosine_similarity_different():
    """Cosine similarity of different random vectors is < 1.0."""
    rng = np.random.RandomState(42)
    vec_a = rng.randn(768).tolist()
    vec_b = rng.randn(768).tolist()
    sim = cosine_similarity(vec_a, vec_b)
    assert sim < 1.0


def test_cosine_similarity_zero_vector():
    """Cosine similarity with zero vector returns 0.0."""
    vec = np.random.randn(768).tolist()
    zero = [0.0] * 768
    sim = cosine_similarity(vec, zero)
    assert sim == 0.0
