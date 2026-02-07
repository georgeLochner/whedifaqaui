from opensearchpy import OpenSearch

from app.core.config import settings


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
