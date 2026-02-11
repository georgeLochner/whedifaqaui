import logging

from app.core.opensearch import SEGMENTS_INDEX, ensure_segments_index, get_opensearch_client
from app.schemas.search import SearchResponse, SearchResult
from app.services.embedding import generate_embeddings

logger = logging.getLogger(__name__)


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    total_seconds = int(seconds)
    minutes = total_seconds // 60
    secs = total_seconds % 60
    return f"{minutes}:{secs:02d}"


def build_hybrid_query(query_text: str, query_embedding: list[float], limit: int = 10) -> dict:
    """Construct an OpenSearch hybrid query with BM25 + kNN.

    Uses a bool/should for the BM25 text match and a top-level knn clause
    for vector similarity. OpenSearch merges these internally.
    """
    return {
        "size": limit,
        "query": {
            "bool": {
                "should": [
                    {"match": {"text": {"query": query_text, "boost": 1.0}}},
                ]
            }
        },
        "knn": {
            "embedding": {
                "vector": query_embedding,
                "k": limit,
            }
        },
    }


def _apply_rrf(bm25_hits: list[dict], knn_hits: list[dict], k: int = 60) -> list[dict]:
    """Combine two ranked lists using Reciprocal Rank Fusion.

    score(doc) = sum(1 / (k + rank_i)) across all lists where doc appears.
    Returns docs sorted by combined RRF score descending.
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, hit in enumerate(bm25_hits, start=1):
        doc_id = hit["_id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        docs[doc_id] = hit

    for rank, hit in enumerate(knn_hits, start=1):
        doc_id = hit["_id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        docs[doc_id] = hit

    sorted_ids = sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True)
    return [{"_id": doc_id, "_source": docs[doc_id]["_source"], "_rrf_score": scores[doc_id]} for doc_id in sorted_ids]


def search(query: str, limit: int = 10) -> SearchResponse:
    """Execute hybrid search: embed query, search OpenSearch, rank with RRF.

    Returns empty SearchResponse for empty queries.
    """
    if not query or not query.strip():
        return SearchResponse(count=0, results=[])

    query = query.strip()

    # Generate embedding for the query text
    embeddings = generate_embeddings([query])
    query_embedding = embeddings[0]

    client = get_opensearch_client()
    ensure_segments_index(client)

    # Run BM25 text search
    bm25_body = {
        "size": limit,
        "query": {"match": {"text": {"query": query}}},
    }
    bm25_response = client.search(index=SEGMENTS_INDEX, body=bm25_body)
    bm25_hits = bm25_response["hits"]["hits"]

    # Run kNN vector search (min_score filters out low-relevance results)
    knn_body = {
        "size": limit,
        "min_score": 0.75,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": limit,
                }
            }
        },
    }
    knn_response = client.search(index=SEGMENTS_INDEX, body=knn_body)
    knn_hits = knn_response["hits"]["hits"]

    # Combine with Reciprocal Rank Fusion
    merged = _apply_rrf(bm25_hits, knn_hits)[:limit]

    # Format results
    results = []
    for hit in merged:
        src = hit["_source"]
        results.append(SearchResult(
            segment_id=src.get("id", hit["_id"]),
            video_id=src["video_id"],
            video_title=src.get("video_title", ""),
            text=src["text"],
            start_time=src["start_time"],
            end_time=src["end_time"],
            speaker=src.get("speaker"),
            score=hit["_rrf_score"],
            timestamp_formatted=_format_timestamp(src["start_time"]),
        ))

    return SearchResponse(count=len(results), results=results)
