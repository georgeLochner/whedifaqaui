import json
import logging
import re
import uuid
from pathlib import Path

from app.schemas.chat import ChatResponse, Citation
from app.schemas.search import SearchResult
from app.services.claude import ClaudeError, claude
from app.services.prompt import QUICK_MODE_PROMPT
from app.services.search import search

logger = logging.getLogger(__name__)

TEMP_DIR = Path("/data/temp")
MAX_CONTEXT_CHARS = 32000  # ~8000 tokens, context truncation limit

CITATION_PATTERN = re.compile(r"\[([^\]]+?)\s*@\s*(\d{1,2}:\d{2})\]")
MIN_RELEVANCE_SCORE = 0.005  # Below single-list RRF min of 1/61 ≈ 0.0164

# Common words excluded from keyword overlap check
_STOP_WORDS = frozenset(
    "a an the is are was were be been being do does did have has had "
    "will would shall should can could may might must "
    "i me my we our us you your he she it they them their "
    "this that these those what which who whom how when where why "
    "in on at to for of with by from up out about into over after "
    "and or but not so if then than too also very "
    "discuss discussed talk talked said tell told meeting "
    "any some all each every no".split()
)


def _has_keyword_overlap(query: str, results: list[SearchResult]) -> bool:
    """Check if the query's distinctive terms appear in any result text.

    Returns False when none of the query's non-stopword terms appear in the
    combined result text, indicating the results are likely false positives
    from semantic similarity rather than genuine matches.
    """
    query_terms = {w.lower() for w in re.findall(r"[a-zA-Z]+", query)} - _STOP_WORDS
    # Remove very short words that are likely not meaningful
    query_terms = {t for t in query_terms if len(t) >= 3}
    if not query_terms:
        return True  # Only stopwords in query; cannot determine relevance
    combined_text = " ".join(r.text.lower() for r in results)
    return any(term in combined_text for term in query_terms)


def _mmss_to_seconds(mmss: str) -> float:
    """Convert MM:SS string to float seconds."""
    parts = mmss.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def truncate_context(segments: list[dict], max_chars: int = MAX_CONTEXT_CHARS) -> list[dict]:
    """Truncate segment list so total text length stays under max_chars.

    Returns the prefix of segments whose cumulative text fits within the limit.
    """
    result = []
    total = 0
    for seg in segments:
        text_len = len(seg.get("text", ""))
        if total + text_len > max_chars and result:
            break
        result.append(seg)
        total += text_len
    return result


def prepare_context_file(segments: list[SearchResult], query: str) -> str:
    """Write search results as a JSON context file for Claude.

    Args:
        segments: Search results to include as context.
        query: The user's original query.

    Returns:
        Absolute file path of the created context file.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    seg_dicts = [
        {
            "video_id": s.video_id,
            "video_title": s.video_title,
            "timestamp": s.start_time,
            "text": s.text,
            "speaker": s.speaker,
            "recording_date": s.recording_date,
        }
        for s in segments
    ]

    seg_dicts = truncate_context(seg_dicts, MAX_CONTEXT_CHARS)

    context = {"query": query, "segments": seg_dicts}

    file_path = TEMP_DIR / f"context_{uuid.uuid4()}.json"
    file_path.write_text(json.dumps(context, indent=2))

    return str(file_path)


def cleanup_context_file(file_path: str) -> None:
    """Delete a temporary context file."""
    Path(file_path).unlink(missing_ok=True)


def build_prompt(query: str, context_file_path: str) -> str:
    """Format the quick-mode prompt template with query and context file path."""
    return QUICK_MODE_PROMPT.format(
        context_file_path=context_file_path,
        question=query,
    )


def _match_video_title(cited_title: str, title_to_id: dict[str, str]) -> str | None:
    """Match a cited title against known video titles.

    Tries exact match first, then case-insensitive substring matching
    to handle Claude abbreviating titles (e.g. "Meeting" for "Backdrop CMS Weekly Meeting").
    """
    # Exact match
    if cited_title in title_to_id:
        return title_to_id[cited_title]

    cited_lower = cited_title.lower()
    # Case-insensitive exact match
    for full_title, vid in title_to_id.items():
        if full_title.lower() == cited_lower:
            return vid

    # Substring match: cited title is contained in a known title
    for full_title, vid in title_to_id.items():
        if cited_lower in full_title.lower():
            return vid

    # If only one video in results, assume the citation refers to it
    unique_ids = list(set(title_to_id.values()))
    if len(unique_ids) == 1:
        return unique_ids[0]

    return None


def extract_citations(
    response_text: str, search_results: list[SearchResult]
) -> list[Citation]:
    """Extract [Video Title @ MM:SS] citations from Claude's response.

    Matches citation patterns against search_results to resolve video_id.
    Returns an empty list when no citations are found.
    """
    matches = CITATION_PATTERN.findall(response_text)
    if not matches:
        return []

    # Build a lookup from video title -> video_id
    title_to_id: dict[str, str] = {}
    for sr in search_results:
        title_to_id[sr.video_title] = sr.video_id

    citations = []
    for title, mmss in matches:
        video_id = _match_video_title(title, title_to_id)
        if video_id is None:
            continue
        timestamp = _mmss_to_seconds(mmss)
        # Find search result with closest timestamp for this video
        text = ""
        resolved_title = title
        best_dist = float("inf")
        for sr in search_results:
            if sr.video_id == video_id:
                dist = abs(sr.start_time - timestamp)
                if dist < best_dist:
                    best_dist = dist
                    text = sr.text
                    resolved_title = sr.video_title
        citations.append(
            Citation(
                video_id=video_id,
                video_title=resolved_title,
                timestamp=timestamp,
                text=text,
            )
        )

    return citations


def deduplicate_citations(citations: list[Citation]) -> list[Citation]:
    """Remove duplicate citations (same video_id + timestamp), preserving order."""
    seen: set[tuple[str, float]] = set()
    result = []
    for c in citations:
        key = (c.video_id, c.timestamp)
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result


def handle_chat_message(
    message: str, conversation_id: str | None = None
) -> ChatResponse:
    """Orchestrate the full chat flow: search → context → Claude → response.

    Args:
        message: The user's chat message.
        conversation_id: Optional ID to resume an existing conversation.

    Returns:
        ChatResponse with Claude's answer, conversation ID, and citations.

    Raises:
        ClaudeError: If the Claude CLI invocation fails.
    """
    # 1. Search OpenSearch for relevant segments, filter by relevance
    search_response = search(message)
    search_results = [r for r in search_response.results if r.score >= MIN_RELEVANCE_SCORE]
    # Drop results when no query keywords appear in result text (false positives)
    if search_results and not _has_keyword_overlap(message, search_results):
        search_results = []

    # 2. Short-circuit when no relevant results
    if not search_results:
        return ChatResponse(
            message="I couldn't find any relevant information about that topic "
            "in the video archive. Try rephrasing your question or asking "
            "about a different topic.",
            conversation_id=conversation_id or str(uuid.uuid4()),
            citations=[],
        )

    # 3. Prepare context file
    context_path = prepare_context_file(search_results, message)

    try:
        # 4. Build prompt
        prompt = build_prompt(message, context_path)

        # 5. Call Claude
        claude_response = claude.query(prompt, conversation_id=conversation_id)

        # 6. Extract and deduplicate citations
        citations = extract_citations(claude_response.result, search_results)
        citations = deduplicate_citations(citations)

        return ChatResponse(
            message=claude_response.result,
            conversation_id=claude_response.conversation_id,
            citations=citations,
        )
    finally:
        # 7. Always clean up temp file
        cleanup_context_file(context_path)
