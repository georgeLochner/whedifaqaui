import enum


class VideoStatus(str, enum.Enum):
    """Status values for video processing pipeline."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TRANSCRIBING = "transcribing"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"
