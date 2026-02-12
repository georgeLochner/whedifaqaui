from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentRequest(BaseModel):
    """Request body for document generation."""

    request: str = Field(..., min_length=1)
    source_video_ids: list[str] | None = None
    format: str = "markdown"


class DocumentResponse(BaseModel):
    """Response after creating a document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    preview: str
    source_count: int
    created_at: datetime


class DocumentDetail(BaseModel):
    """Full document detail including content."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    source_video_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
