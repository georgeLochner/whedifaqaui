from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A citation linking to a specific video segment."""

    video_id: str
    video_title: str
    timestamp: float = Field(..., ge=0)
    text: str


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    message: str = Field(..., min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    message: str
    conversation_id: str
    citations: list[Citation] = Field(default_factory=list)
