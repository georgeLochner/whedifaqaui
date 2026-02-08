import logging
import re
from collections import Counter

from app.services.embedding import cosine_similarity, generate_embeddings

logger = logging.getLogger(__name__)


def semantic_chunk(
    segments: list[dict],
    similarity_threshold: float = 0.5,
    min_chunk_tokens: int = 100,
    max_chunk_tokens: int = 500,
) -> list[dict]:
    """Group transcript segments into semantically coherent chunks.

    Args:
        segments: List of dicts with keys: text, start_time, end_time, speaker
        similarity_threshold: Cosine similarity below which a boundary is placed
        min_chunk_tokens: Minimum words per chunk (merge smaller ones)
        max_chunk_tokens: Maximum words per chunk (split larger ones)

    Returns:
        List of chunk dicts: [{text, start_time, end_time, speaker, embedding}]
    """
    if not segments:
        return []

    if len(segments) == 1:
        embeddings = generate_embeddings([segments[0]["text"]])
        return [{
            "text": segments[0]["text"],
            "start_time": segments[0]["start_time"],
            "end_time": segments[0]["end_time"],
            "speaker": segments[0].get("speaker", "SPEAKER_00"),
            "embedding": embeddings[0],
        }]

    # Step 1: Generate embeddings for each segment
    texts = [seg["text"] for seg in segments]
    embeddings = generate_embeddings(texts)

    # Step 2: Compute cosine similarity between consecutive segments
    similarities = []
    for i in range(len(embeddings) - 1):
        sim = cosine_similarity(embeddings[i], embeddings[i + 1])
        similarities.append(sim)

    # Step 3: Identify boundary indices where similarity drops below threshold
    boundaries = set()
    for i, sim in enumerate(similarities):
        if sim < similarity_threshold:
            boundaries.add(i + 1)  # boundary before segment i+1

    # Step 4: Group segments between boundaries into chunks
    groups = []
    current_group = [0]
    for i in range(1, len(segments)):
        if i in boundaries:
            groups.append(current_group)
            current_group = [i]
        else:
            current_group.append(i)
    groups.append(current_group)

    # Build initial chunks from groups
    chunks = _build_chunks_from_groups(segments, groups)

    # Step 5: Merge small chunks with neighbors
    chunks = _merge_small_chunks(chunks, min_chunk_tokens)

    # Step 6: Split large chunks at sentence boundaries
    chunks = _split_large_chunks(chunks, max_chunk_tokens)

    # Step 7: Re-embed final chunk texts
    chunk_texts = [c["text"] for c in chunks]
    final_embeddings = generate_embeddings(chunk_texts)
    for chunk, emb in zip(chunks, final_embeddings):
        chunk["embedding"] = emb

    logger.info(
        "Semantic chunking: %d segments → %d chunks", len(segments), len(chunks)
    )
    return chunks


def _build_chunks_from_groups(
    segments: list[dict], groups: list[list[int]]
) -> list[dict]:
    """Build chunk dicts from segment index groups."""
    chunks = []
    for group in groups:
        group_segments = [segments[i] for i in group]
        text = " ".join(seg["text"] for seg in group_segments)
        chunks.append({
            "text": text,
            "start_time": group_segments[0]["start_time"],
            "end_time": group_segments[-1]["end_time"],
            "speaker": _majority_speaker(group_segments),
            "_segments": group_segments,
        })
    return chunks


def _count_tokens(text: str) -> int:
    """Approximate token count using whitespace split."""
    return len(text.split())


def _merge_small_chunks(chunks: list[dict], min_tokens: int) -> list[dict]:
    """Merge chunks smaller than min_tokens with their nearest neighbor."""
    if len(chunks) <= 1:
        return chunks

    merged = []
    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        if _count_tokens(chunk["text"]) < min_tokens and merged:
            # Merge with previous chunk
            prev = merged[-1]
            prev["text"] = prev["text"] + " " + chunk["text"]
            prev["end_time"] = chunk["end_time"]
            all_segs = prev.get("_segments", []) + chunk.get("_segments", [])
            prev["speaker"] = _majority_speaker(all_segs)
            prev["_segments"] = all_segs
        elif _count_tokens(chunk["text"]) < min_tokens and not merged and i + 1 < len(chunks):
            # Merge with next chunk
            nxt = chunks[i + 1]
            nxt["text"] = chunk["text"] + " " + nxt["text"]
            nxt["start_time"] = chunk["start_time"]
            all_segs = chunk.get("_segments", []) + nxt.get("_segments", [])
            nxt["speaker"] = _majority_speaker(all_segs)
            nxt["_segments"] = all_segs
        else:
            merged.append(chunk)
        i += 1

    # Clean up internal _segments field
    for chunk in merged:
        chunk.pop("_segments", None)
    return merged


def _split_large_chunks(chunks: list[dict], max_tokens: int) -> list[dict]:
    """Split chunks exceeding max_tokens at sentence boundaries."""
    result = []
    for chunk in chunks:
        if _count_tokens(chunk["text"]) <= max_tokens:
            result.append(chunk)
            continue

        # Split at sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', chunk["text"])
        sub_chunks = []
        current_text = ""

        for sentence in sentences:
            candidate = (current_text + " " + sentence).strip() if current_text else sentence
            if _count_tokens(candidate) > max_tokens and current_text:
                sub_chunks.append(current_text)
                current_text = sentence
            else:
                current_text = candidate

        if current_text:
            sub_chunks.append(current_text)

        # Distribute timestamps proportionally across sub-chunks
        total_duration = chunk["end_time"] - chunk["start_time"]
        total_tokens = _count_tokens(chunk["text"])
        time_offset = chunk["start_time"]

        for sub_text in sub_chunks:
            sub_tokens = _count_tokens(sub_text)
            proportion = sub_tokens / total_tokens if total_tokens > 0 else 1.0 / len(sub_chunks)
            sub_duration = total_duration * proportion

            result.append({
                "text": sub_text,
                "start_time": time_offset,
                "end_time": time_offset + sub_duration,
                "speaker": chunk.get("speaker", "SPEAKER_00"),
            })
            time_offset += sub_duration

    return result


def _majority_speaker(segments: list[dict]) -> str:
    """Return the most common speaker label from a list of segments."""
    speakers = [seg.get("speaker", "SPEAKER_00") or "SPEAKER_00" for seg in segments]
    if not speakers:
        return "SPEAKER_00"
    counter = Counter(speakers)
    return counter.most_common(1)[0][0]
