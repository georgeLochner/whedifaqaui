import logging

from opensearchpy import OpenSearch

from app.core.config import settings

logger = logging.getLogger(__name__)

SEGMENTS_INDEX = "segments_index"

SEGMENTS_INDEX_BODY = {
    "settings": {
        "index": {
            "knn": True,
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "video_id": {"type": "keyword"},
            "video_title": {"type": "text"},
            "transcript_id": {"type": "keyword"},
            "text": {"type": "text", "analyzer": "english"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 768,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene",
                    "parameters": {
                        "ef_construction": 128,
                        "m": 16,
                    },
                },
            },
            "start_time": {"type": "float"},
            "end_time": {"type": "float"},
            "speaker": {"type": "keyword"},
            "recording_date": {"type": "date"},
            "created_at": {"type": "date"},
        }
    },
}


def get_opensearch_client() -> OpenSearch:
    """Create and return an OpenSearch client."""
    # Parse URL to extract host and port
    url = settings.OPENSEARCH_URL
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]

    host, port = url.split(":") if ":" in url else (url, 9200)

    client = OpenSearch(
        hosts=[{"host": host, "port": int(port)}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )

    return client


def ensure_segments_index(client: OpenSearch) -> None:
    """Create the segments index if it does not exist."""
    if not client.indices.exists(index=SEGMENTS_INDEX):
        client.indices.create(index=SEGMENTS_INDEX, body=SEGMENTS_INDEX_BODY)
        logger.info("Created OpenSearch index: %s", SEGMENTS_INDEX)
