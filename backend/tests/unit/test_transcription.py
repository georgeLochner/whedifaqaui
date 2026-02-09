"""Tests for transcription parsing (V2-U01 to V2-U04) and FFmpeg processing (P1-U01, P1-U02)."""

from unittest.mock import MagicMock, patch

from app.services.transcription import calculate_word_count, parse_whisperx_output


# ---------------------------------------------------------------------------
# V2-U01: WhisperX output parsing
# ---------------------------------------------------------------------------


def test_whisperx_output_parsing():
    """V2-U01: parse_whisperx_output extracts segments correctly."""
    raw = {
        "segments": [
            {"start": 0.0, "end": 3.5, "text": "Hello everyone", "speaker": "SPEAKER_00"},
            {"start": 3.5, "end": 7.2, "text": "Welcome to the meeting", "speaker": "SPEAKER_01"},
            {"start": 7.2, "end": 10.0, "text": "Let us begin", "speaker": "SPEAKER_00"},
        ]
    }
    segments = parse_whisperx_output(raw)

    assert len(segments) == 3
    assert segments[0]["text"] == "Hello everyone"
    assert segments[1]["text"] == "Welcome to the meeting"
    assert segments[2]["text"] == "Let us begin"
    # Each segment has required keys
    for seg in segments:
        assert set(seg.keys()) == {"start", "end", "text", "speaker"}


def test_whisperx_output_skips_empty_text():
    """parse_whisperx_output skips segments with empty text."""
    raw = {
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "   ", "speaker": "SPEAKER_00"},
            {"start": 1.0, "end": 2.0, "text": "Valid segment", "speaker": "SPEAKER_00"},
            {"start": 2.0, "end": 3.0, "text": "", "speaker": "SPEAKER_00"},
        ]
    }
    segments = parse_whisperx_output(raw)
    assert len(segments) == 1
    assert segments[0]["text"] == "Valid segment"


def test_whisperx_output_skips_no_timestamps():
    """parse_whisperx_output skips segments with no timestamps at all."""
    raw = {
        "segments": [
            {"text": "No timestamps here", "speaker": "SPEAKER_00"},
            {"start": 1.0, "end": 2.0, "text": "Has timestamps", "speaker": "SPEAKER_00"},
        ]
    }
    segments = parse_whisperx_output(raw)
    assert len(segments) == 1
    assert segments[0]["text"] == "Has timestamps"


# ---------------------------------------------------------------------------
# V2-U02: Segment timestamp extraction
# ---------------------------------------------------------------------------


def test_segment_timestamp_extraction():
    """V2-U02: Timestamps are float values in seconds."""
    raw = {
        "segments": [
            {"start": 0, "end": 5, "text": "First", "speaker": "SPEAKER_00"},
            {"start": 5.123, "end": 10.456, "text": "Second", "speaker": "SPEAKER_00"},
        ]
    }
    segments = parse_whisperx_output(raw)

    assert isinstance(segments[0]["start"], float)
    assert isinstance(segments[0]["end"], float)
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] == 5.0
    assert segments[1]["start"] == 5.123
    assert segments[1]["end"] == 10.456


def test_segment_partial_timestamp_handling():
    """parse_whisperx_output fills in partial timestamps."""
    raw = {
        "segments": [
            {"start": None, "end": 5.0, "text": "Missing start", "speaker": "SPEAKER_00"},
            {"start": 6.0, "end": None, "text": "Missing end", "speaker": "SPEAKER_00"},
        ]
    }
    segments = parse_whisperx_output(raw)
    assert len(segments) == 2
    # Missing start defaults to end
    assert segments[0]["start"] == 5.0
    assert segments[0]["end"] == 5.0
    # Missing end defaults to start
    assert segments[1]["start"] == 6.0
    assert segments[1]["end"] == 6.0


# ---------------------------------------------------------------------------
# V2-U03: Speaker label extraction
# ---------------------------------------------------------------------------


def test_speaker_label_extraction():
    """V2-U03: Speaker labels in SPEAKER_XX format are preserved."""
    raw = {
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "Hello", "speaker": "SPEAKER_00"},
            {"start": 1.0, "end": 2.0, "text": "Hi", "speaker": "SPEAKER_01"},
            {"start": 2.0, "end": 3.0, "text": "Hey", "speaker": "SPEAKER_02"},
        ]
    }
    segments = parse_whisperx_output(raw)

    assert segments[0]["speaker"] == "SPEAKER_00"
    assert segments[1]["speaker"] == "SPEAKER_01"
    assert segments[2]["speaker"] == "SPEAKER_02"


def test_missing_speaker_defaults():
    """V2-U03: Missing speaker defaults to SPEAKER_00."""
    raw = {
        "segments": [
            {"start": 0.0, "end": 1.0, "text": "No speaker key"},
            {"start": 1.0, "end": 2.0, "text": "Null speaker", "speaker": None},
            {"start": 2.0, "end": 3.0, "text": "Empty speaker", "speaker": ""},
        ]
    }
    segments = parse_whisperx_output(raw)

    assert segments[0]["speaker"] == "SPEAKER_00"
    assert segments[1]["speaker"] == "SPEAKER_00"
    assert segments[2]["speaker"] == "SPEAKER_00"


# ---------------------------------------------------------------------------
# V2-U04: Word count calculation
# ---------------------------------------------------------------------------


def test_word_count_calculation():
    """V2-U04: calculate_word_count sums words across segments."""
    segments = [
        {"text": "Hello everyone"},           # 2 words
        {"text": "Welcome to the meeting"},    # 4 words
        {"text": "Let us begin"},              # 3 words
    ]
    assert calculate_word_count(segments) == 9


def test_word_count_empty():
    """calculate_word_count returns 0 for empty list."""
    assert calculate_word_count([]) == 0


# ---------------------------------------------------------------------------
# P1-U01: Video transcode to MP4
# ---------------------------------------------------------------------------


@patch("app.services.ffmpeg.subprocess.run")
@patch("app.services.ffmpeg.Path")
def test_video_transcode_to_mp4(mock_path, mock_run):
    """P1-U01: remux_to_mp4 calls ffmpeg with correct args and returns True."""
    from app.services.ffmpeg import remux_to_mp4

    mock_run.return_value = MagicMock(returncode=0)
    mock_path.return_value.parent.mkdir = MagicMock()

    result = remux_to_mp4("/input/video.mkv", "/output/video.mp4")

    assert result is True
    # First call should be stream copy attempt
    first_call_args = mock_run.call_args_list[0]
    cmd = first_call_args[0][0]
    assert cmd[0] == "ffmpeg"
    assert "-i" in cmd
    assert "/input/video.mkv" in cmd
    assert "/output/video.mp4" in cmd


@patch("app.services.ffmpeg.subprocess.run")
@patch("app.services.ffmpeg.Path")
def test_video_transcode_fallback(mock_path, mock_run):
    """P1-U01: remux_to_mp4 falls back to transcode when copy fails."""
    from app.services.ffmpeg import remux_to_mp4

    # First call fails (stream copy), second succeeds (transcode)
    mock_run.side_effect = [
        MagicMock(returncode=1),
        MagicMock(returncode=0),
    ]
    mock_path.return_value.parent.mkdir = MagicMock()

    result = remux_to_mp4("/input/video.mkv", "/output/video.mp4")

    assert result is True
    assert mock_run.call_count == 2
    # Second call should use libx264
    second_call_args = mock_run.call_args_list[1]
    cmd = second_call_args[0][0]
    assert "libx264" in cmd


# ---------------------------------------------------------------------------
# P1-U02: Processed path stored on video record
# ---------------------------------------------------------------------------


@patch("app.tasks.video_processing.update_status")
@patch("app.tasks.video_processing.ffmpeg")
@patch("app.tasks.video_processing.SessionLocal")
def test_processed_path_stored(mock_session_local, mock_ffmpeg, mock_update_status):
    """P1-U02: process_video task sets processed_path on video record."""
    import uuid

    from app.tasks.video_processing import process_video

    video_id = str(uuid.uuid4())
    mock_video = MagicMock()
    mock_video.file_path = "/data/videos/original/test.mkv"

    mock_db = MagicMock()
    mock_db.get.return_value = mock_video
    mock_session_local.return_value = mock_db

    mock_ffmpeg.remux_to_mp4.return_value = True
    mock_ffmpeg.generate_thumbnail.return_value = True
    mock_ffmpeg.extract_audio.return_value = True
    mock_ffmpeg.get_duration.return_value = 120.0

    result = process_video(video_id)

    assert result["status"] == "processing_complete"
    # processed_path should be set on the video object
    assert mock_video.processed_path is not None
    assert video_id in mock_video.processed_path
    assert mock_video.processed_path.endswith(".mp4")
