from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result from a video segment."""

    segment_id: str
    video_id: str
    video_title: str
    text: str
    start_time: float
    end_time: float
    speaker: str | None = None
    score: float
    timestamp_formatted: str


class SearchResponse(BaseModel):
    """Response containing ranked search results."""

    count: int = Field(default=0, ge=0)
    results: list[SearchResult] = Field(default_factory=list)
