import logging
import os

logger = logging.getLogger(__name__)

# Module-level cache for loaded model
_whisperx_model = None


def _patch_torch_load():
    """Patch torch.load for PyTorch 2.6+ compatibility with WhisperX/pyannote models.

    PyTorch 2.6 changed torch.load to default weights_only=True, which breaks
    loading pyannote and other models that use pickle-based serialization.
    """
    import functools

    import torch

    if not hasattr(torch.load, "_patched_for_whisperx"):
        _original_torch_load = torch.load

        @functools.wraps(_original_torch_load)
        def _patched_load(*args, **kwargs):
            if kwargs.get("weights_only") is None:
                kwargs["weights_only"] = False
            return _original_torch_load(*args, **kwargs)

        _patched_load._patched_for_whisperx = True
        torch.load = _patched_load


def load_whisperx_model(
    device: str = "cpu", compute_type: str = "int8"
):
    """Load WhisperX (faster-whisper) model, caching to avoid reloads."""
    global _whisperx_model
    if _whisperx_model is not None:
        return _whisperx_model

    _patch_torch_load()
    import whisperx

    model_name = os.environ.get("WHISPER_MODEL", "medium")
    logger.info("Loading WhisperX model '%s' on %s (%s)", model_name, device, compute_type)
    _whisperx_model = whisperx.load_model(
        model_name, device, compute_type=compute_type
    )
    return _whisperx_model


def transcribe_audio(
    audio_path: str, device: str = "cpu", hf_token: str | None = None
) -> dict:
    """Run full WhisperX workflow: transcribe → align → diarize.

    Returns the WhisperX result dict containing 'segments' and other metadata.
    """
    import whisperx

    # Step 1: Load model and transcribe
    model = load_whisperx_model(device=device)
    result = model.transcribe(audio_path, batch_size=16)
    logger.info("Transcription complete: %d raw segments", len(result.get("segments", [])))

    # Step 2: Align segments for accurate timestamps
    language = result.get("language", "en")
    align_model, align_metadata = whisperx.load_align_model(
        language_code=language, device=device
    )
    result = whisperx.align(
        result["segments"], align_model, align_metadata, audio_path, device
    )
    logger.info("Alignment complete")

    # Step 3: Speaker diarization (if HuggingFace token provided)
    if hf_token:
        try:
            diarize_pipeline = whisperx.DiarizationPipeline(
                use_auth_token=hf_token, device=device
            )
            diarize_segments = diarize_pipeline(audio_path)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            logger.info("Speaker diarization complete")
        except Exception as e:
            logger.warning("Speaker diarization failed, continuing without: %s", e)
    else:
        logger.info("No HF token provided, skipping speaker diarization")

    return result


def parse_whisperx_output(result: dict) -> list[dict]:
    """Parse WhisperX output into normalized segments.

    Returns list of dicts: [{start, end, text, speaker}, ...]
    Handles missing speakers (defaults to 'SPEAKER_00') and missing timestamps.
    """
    segments = []
    raw_segments = result.get("segments", [])

    for seg in raw_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start = seg.get("start")
        end = seg.get("end")

        # Skip segments with no timestamps at all
        if start is None and end is None:
            continue

        # Handle partially missing timestamps
        if start is None:
            start = end
        if end is None:
            end = start

        speaker = seg.get("speaker", "SPEAKER_00") or "SPEAKER_00"

        segments.append({
            "start": float(start),
            "end": float(end),
            "text": text,
            "speaker": speaker,
        })

    return segments


def calculate_word_count(segments: list[dict]) -> int:
    """Sum word counts across all segments."""
    return sum(len(seg["text"].split()) for seg in segments)
