from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.opensearch import get_opensearch_client
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies connectivity to all services.

    Returns:
        dict: Status of each service (postgres, opensearch, redis)
    """
    status = {"status": "ok", "services": {}}

    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        status["services"]["postgres"] = "connected"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["postgres"] = f"error: {str(e)}"

    # Check OpenSearch
    try:
        client = get_opensearch_client()
        info = client.cluster.health()
        status["services"]["opensearch"] = info.get("status", "unknown")
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["opensearch"] = f"error: {str(e)}"

    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        status["services"]["redis"] = "connected"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["redis"] = f"error: {str(e)}"

    return status
