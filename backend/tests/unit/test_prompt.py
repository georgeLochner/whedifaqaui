"""Unit tests for prompt templates."""

from app.services.prompt import QUICK_MODE_PROMPT, DOCUMENT_PROMPT


def test_quick_mode_prompt_has_placeholders():
    """QUICK_MODE_PROMPT contains {context_file_path} and {question}."""
    assert "{context_file_path}" in QUICK_MODE_PROMPT
    assert "{question}" in QUICK_MODE_PROMPT


def test_document_prompt_has_placeholders():
    """DOCUMENT_PROMPT contains {source_file_path} and {request}."""
    assert "{source_file_path}" in DOCUMENT_PROMPT
    assert "{request}" in DOCUMENT_PROMPT


def test_quick_mode_prompt_format():
    """Template formats correctly with .format()."""
    result = QUICK_MODE_PROMPT.format(
        context_file_path="/data/temp/context_abc.json",
        question="What is the auth system?"
    )
    assert "/data/temp/context_abc.json" in result
    assert "What is the auth system?" in result
    assert "{context_file_path}" not in result
    assert "{question}" not in result


def test_document_prompt_format():
    """Template formats correctly with .format()."""
    result = DOCUMENT_PROMPT.format(
        source_file_path="/data/temp/source_abc.json",
        request="Summarize the meeting"
    )
    assert "/data/temp/source_abc.json" in result
    assert "Summarize the meeting" in result
    assert "{source_file_path}" not in result
    assert "{request}" not in result
