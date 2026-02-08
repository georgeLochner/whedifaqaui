import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def get_duration(input_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        input_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {input_path}: {result.stderr}")
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def remux_to_mp4(input_path: str, output_path: str) -> bool:
    """Remux MKV to MP4. Try fast stream copy first, fall back to transcode."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Try fast copy (stream copy) first
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c", "copy",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode == 0:
        logger.info("Remuxed %s to MP4 (stream copy)", input_path)
        return True

    # Fall back to full transcode
    logger.info("Stream copy failed, transcoding %s", input_path)
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg transcode failed: {result.stderr[:500]}")
    logger.info("Transcoded %s to MP4", input_path)
    return True


def extract_audio(input_path: str, output_path: str) -> bool:
    """Extract audio from video as 16kHz mono WAV for WhisperX."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {result.stderr[:500]}")
    logger.info("Extracted audio from %s", input_path)
    return True


def generate_thumbnail(
    input_path: str, output_path: str, time_percent: float = 0.1
) -> bool:
    """Extract a thumbnail frame at time_percent of duration, resize to 320x180."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    duration = get_duration(input_path)
    timestamp = duration * time_percent

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", input_path,
        "-vframes", "1",
        "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Thumbnail generation failed: {result.stderr[:500]}")
    logger.info("Generated thumbnail for %s at %.1fs", input_path, timestamp)
    return True
