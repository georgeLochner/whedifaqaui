import math

from pydantic import BaseModel, ConfigDict, computed_field


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    start_time: float
    end_time: float
    text: str
    speaker: str | None = None

    @computed_field
    @property
    def timestamp_formatted(self) -> str:
        """Format start_time as MM:SS."""
        total_seconds = int(math.floor(self.start_time))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"


class TranscriptResponse(BaseModel):
    video_id: str
    segments: list[SegmentResponse]
    count: int
