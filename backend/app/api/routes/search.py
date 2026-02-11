import logging

from fastapi import APIRouter, HTTPException, Query
from opensearchpy import ConnectionError as OSConnectionError

from app.schemas.search import SearchResponse
from app.services.search import search as search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query("", description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search indexed video segments with hybrid BM25 + semantic search."""
    if not q or not q.strip():
        return SearchResponse(count=0, results=[])

    try:
        return search_service(q, limit=limit)
    except OSConnectionError:
        raise HTTPException(status_code=503, detail="Search service unavailable")
