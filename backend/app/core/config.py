from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = {"env_file": ".env", "extra": "ignore"}

    # Database
    DATABASE_URL: str = "postgresql://whedifaqaui:devpassword@postgres:5432/whedifaqaui"

    # OpenSearch
    OPENSEARCH_URL: str = "http://opensearch:9200"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"

    # Storage paths
    VIDEO_STORAGE_PATH: str = "/data/videos"
    TRANSCRIPT_STORAGE_PATH: str = "/data/transcripts"


settings = Settings()
