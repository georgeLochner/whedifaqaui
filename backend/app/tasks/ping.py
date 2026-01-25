"""Simple ping task for health checks."""

from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.ping")
def ping() -> str:
    """Return pong - used for health checks."""
    return "pong"
