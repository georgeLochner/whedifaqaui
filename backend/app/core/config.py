from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://whedifaqaui:devpassword@localhost:5432/whedifaqaui"

    # OpenSearch
    opensearch_url: str = "http://localhost:9200"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Data directories
    data_dir: str = "/data"
    videos_dir: str = "/data/videos"
    transcripts_dir: str = "/data/transcripts"
    temp_dir: str = "/data/temp"
    models_dir: str = "/data/models"

    # Application
    debug: bool = True
    app_name: str = "Whedifaqaui"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
