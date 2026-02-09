"""Tests for semantic chunking logic (C1-U01 to C1-U04)."""

import random
from unittest.mock import patch

import numpy as np

from app.services.chunking import (
    _count_tokens,
    _majority_speaker,
    _merge_small_chunks,
    _split_large_chunks,
    semantic_chunk,
)


def _fake_embeddings(texts):
    """Generate deterministic fake 768-dim embeddings based on text hash."""
    result = []
    for text in texts:
        rng = np.random.RandomState(hash(text) % (2**31))
        vec = rng.randn(768).astype(np.float64)
        vec = vec / np.linalg.norm(vec)
        result.append(vec.tolist())
    return result


def _make_segment(text, start_time, end_time, speaker="SPEAKER_00"):
    return {
        "text": text,
        "start_time": start_time,
        "end_time": end_time,
        "speaker": speaker,
    }


# ---------------------------------------------------------------------------
# C1-U01: Chunk size limits
# ---------------------------------------------------------------------------


@patch("app.services.chunking.generate_embeddings", side_effect=_fake_embeddings)
def test_chunk_size_limits(mock_embed):
    """C1-U01: All chunks have between min and max words (within merge/split bounds)."""
    # Create segments with enough text to form multi-word chunks
    segments = []
    for i in range(20):
        # Each segment ~30 words
        words = " ".join(f"word{j}" for j in range(30))
        segments.append(_make_segment(
            text=f"Topic {i} discussion. {words}.",
            start_time=float(i * 10),
            end_time=float(i * 10 + 9),
            speaker=f"SPEAKER_{i % 2:02d}",
        ))

    chunks = semantic_chunk(
        segments,
        similarity_threshold=0.5,
        min_chunk_tokens=50,
        max_chunk_tokens=500,
    )

    assert len(chunks) > 0
    for chunk in chunks:
        word_count = _count_tokens(chunk["text"])
        # Chunks should respect max limit
        assert word_count <= 500, f"Chunk too large: {word_count} words"


# ---------------------------------------------------------------------------
# C1-U02: Chunk preserves speaker
# ---------------------------------------------------------------------------


@patch("app.services.chunking.generate_embeddings", side_effect=_fake_embeddings)
def test_chunk_preserves_speaker(mock_embed):
    """C1-U02: Each chunk has a speaker field."""
    segments = [
        _make_segment("The project architecture uses microservices pattern.", 0.0, 5.0, "SPEAKER_00"),
        _make_segment("Each service communicates via REST APIs.", 5.0, 10.0, "SPEAKER_00"),
        _make_segment("We deployed everything on Kubernetes cluster.", 10.0, 15.0, "SPEAKER_01"),
        _make_segment("The CI CD pipeline runs automated tests.", 15.0, 20.0, "SPEAKER_01"),
    ]

    chunks = semantic_chunk(segments, min_chunk_tokens=1, max_chunk_tokens=500)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "speaker" in chunk
        assert chunk["speaker"].startswith("SPEAKER_")


# ---------------------------------------------------------------------------
# C1-U03: Chunk timestamps valid
# ---------------------------------------------------------------------------


@patch("app.services.chunking.generate_embeddings", side_effect=_fake_embeddings)
def test_chunk_timestamps_valid(mock_embed):
    """C1-U03: start_time < end_time for every chunk."""
    segments = [
        _make_segment("First topic about databases and storage.", 0.0, 10.0, "SPEAKER_00"),
        _make_segment("Second topic about frontend frameworks.", 10.0, 20.0, "SPEAKER_01"),
        _make_segment("Third topic about deployment strategies.", 20.0, 30.0, "SPEAKER_00"),
        _make_segment("Fourth topic about testing approaches.", 30.0, 40.0, "SPEAKER_01"),
    ]

    chunks = semantic_chunk(segments, min_chunk_tokens=1, max_chunk_tokens=500)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["start_time"] < chunk["end_time"], (
            f"Invalid timestamps: start={chunk['start_time']}, end={chunk['end_time']}"
        )


# ---------------------------------------------------------------------------
# C1-U04: Semantic boundary detection
# ---------------------------------------------------------------------------


@patch("app.services.chunking.generate_embeddings")
def test_semantic_boundary_detection(mock_embed):
    """C1-U04: Chunks split at topic boundary when similarity is low."""
    # Two groups of segments on very different topics.
    # We control embeddings so group A is similar to itself and different from group B.
    vec_a = np.zeros(768)
    vec_a[0] = 1.0  # unit vector pointing in one direction
    vec_b = np.zeros(768)
    vec_b[1] = 1.0  # orthogonal unit vector

    # First call: per-segment embeddings; second call: per-chunk re-embeddings
    # Group A gets vec_a, group B gets vec_b
    def side_effect(texts):
        result = []
        for t in texts:
            if "cooking" in t.lower() or "recipe" in t.lower():
                result.append(vec_b.tolist())
            else:
                result.append(vec_a.tolist())
        return result

    mock_embed.side_effect = side_effect

    segments = [
        _make_segment("Software engineering best practices for teams.", 0.0, 5.0),
        _make_segment("Code review processes improve software quality.", 5.0, 10.0),
        _make_segment("Cooking recipes for Italian pasta dishes.", 10.0, 15.0),
        _make_segment("Recipe for homemade tomato sauce and basil.", 15.0, 20.0),
    ]

    chunks = semantic_chunk(
        segments,
        similarity_threshold=0.5,
        min_chunk_tokens=1,
        max_chunk_tokens=500,
    )

    # Should split into at least 2 chunks at the topic boundary
    assert len(chunks) >= 2
    # First chunk should contain software text, last should contain cooking text
    assert "software" in chunks[0]["text"].lower() or "code" in chunks[0]["text"].lower()
    last_chunk = chunks[-1]
    assert "cooking" in last_chunk["text"].lower() or "recipe" in last_chunk["text"].lower()


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


def test_count_tokens():
    """_count_tokens counts words via whitespace split."""
    assert _count_tokens("hello world") == 2
    assert _count_tokens("one two three four five") == 5
    assert _count_tokens("") == 0


def test_majority_speaker():
    """_majority_speaker returns the most common speaker."""
    segments = [
        {"speaker": "SPEAKER_00"},
        {"speaker": "SPEAKER_01"},
        {"speaker": "SPEAKER_00"},
    ]
    assert _majority_speaker(segments) == "SPEAKER_00"


def test_majority_speaker_missing():
    """_majority_speaker handles missing speaker keys."""
    segments = [{"text": "no speaker key"}, {"speaker": None}]
    assert _majority_speaker(segments) == "SPEAKER_00"
