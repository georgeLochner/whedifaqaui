import logging

import numpy as np

logger = logging.getLogger(__name__)

# Module-level cache for loaded model
_embedding_model = None


def load_embedding_model(model_name: str = "BAAI/bge-base-en-v1.5"):
    """Load and cache the BGE sentence-transformer model."""
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model

    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model: %s", model_name)
    _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def generate_embeddings(
    texts: list[str], model=None
) -> list[list[float]]:
    """Batch encode texts into 768-dim float vectors.

    Loads model automatically if not provided.
    """
    if not texts:
        return []

    if model is None:
        model = load_embedding_model()

    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return [emb.tolist() for emb in embeddings]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a, dtype=np.float64)
    b = np.array(vec_b, dtype=np.float64)

    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(dot / (norm_a * norm_b))
