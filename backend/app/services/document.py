"""Document generation service.

Fetches transcript content, builds a document prompt, calls Claude,
and saves the generated document to the database.
"""

import json
import logging
import re
import uuid as uuid_mod
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import GeneratedDocument
from app.models.transcript import Transcript
from app.models.video import Video
from app.schemas.document import DocumentRequest
from app.services.claude import claude

logger = logging.getLogger(__name__)

TEMP_DIR = Path("/data/temp")
MAX_CONTEXT_CHARS = 64000  # Larger budget for full transcript context

DOCUMENT_PROMPT = """Generate a summary document based on video transcript content.

READ THE SOURCE FILE: {source_file_path}

The file contains transcript segments to summarize.

User Request: {request}

Instructions:
- Read the source file first
- Create a well-structured markdown document
- Include a title as the first line (# Title)
- Include sections as appropriate
- Cite timestamps for key points using [MM:SS] format
- Be comprehensive but avoid unnecessary repetition"""


def prepare_document_context(video_ids: list[str] | None, db: Session) -> tuple[str, list[UUID]]:
    """Fetch transcripts for the given video IDs and write to a temp context file.

    Args:
        video_ids: List of video ID strings to fetch transcripts for.
                   If None or empty, fetches all available transcripts.
        db: Database session.

    Returns:
        Tuple of (context file path, list of resolved video UUIDs).
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    query = db.query(Transcript)
    if video_ids:
        uuid_ids = [UUID(vid) for vid in video_ids]
        query = query.filter(Transcript.video_id.in_(uuid_ids))

    transcripts = query.all()

    # Also fetch video titles for context
    resolved_video_ids = [t.video_id for t in transcripts]
    videos = {}
    if resolved_video_ids:
        video_rows = db.query(Video).filter(Video.id.in_(resolved_video_ids)).all()
        videos = {v.id: v.title for v in video_rows}

    context_entries = []
    for t in transcripts:
        context_entries.append({
            "video_id": str(t.video_id),
            "video_title": videos.get(t.video_id, "Unknown"),
            "text": t.full_text[:MAX_CONTEXT_CHARS],
        })

    context = {"transcripts": context_entries}

    file_path = TEMP_DIR / f"doc_context_{uuid_mod.uuid4()}.json"
    file_path.write_text(json.dumps(context, indent=2))

    return str(file_path), resolved_video_ids


def cleanup_context_file(file_path: str) -> None:
    """Delete a temporary context file."""
    Path(file_path).unlink(missing_ok=True)


def build_document_prompt(request: str, source_file_path: str) -> str:
    """Format the document generation prompt template."""
    return DOCUMENT_PROMPT.format(
        source_file_path=source_file_path,
        request=request,
    )


def extract_title(content: str) -> str:
    """Extract title from markdown content.

    Looks for the first markdown heading (# Title). If not found,
    uses the first non-empty line. Falls back to 'Generated Document'.
    """
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^#+\s+(.+)$", line)
        if match:
            return match.group(1).strip()
        return line[:255]
    return "Generated Document"


def generate_document(
    request: DocumentRequest,
    session_id: str | None,
    db: Session,
) -> GeneratedDocument:
    """Generate a summary document using Claude.

    Args:
        request: The document generation request.
        session_id: Browser/user session ID for linking documents.
        db: Database session.

    Returns:
        The saved GeneratedDocument instance.

    Raises:
        ClaudeError: If Claude CLI invocation fails.
        subprocess.TimeoutExpired: If Claude times out.
    """
    # 1. Prepare context file with transcript content
    context_path, resolved_video_ids = prepare_document_context(
        request.source_video_ids, db
    )

    try:
        # 2. Build prompt
        prompt = build_document_prompt(request.request, context_path)

        # 3. Call Claude
        claude_response = claude.query(prompt, timeout=180)

        # 4. Extract title from generated content
        content = claude_response.result
        title = extract_title(content)

        # 5. Save to database
        doc = GeneratedDocument(
            session_id=session_id,
            title=title,
            content=content,
            source_video_ids=resolved_video_ids or None,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info(f"Generated document '{title}' (id={doc.id})")
        return doc
    finally:
        # 6. Always clean up temp file
        cleanup_context_file(context_path)


def get_document(document_id: UUID, db: Session) -> GeneratedDocument | None:
    """Fetch a document by ID from the database.

    Args:
        document_id: UUID of the document.
        db: Database session.

    Returns:
        GeneratedDocument if found, None otherwise.
    """
    return db.query(GeneratedDocument).filter(
        GeneratedDocument.id == document_id
    ).first()
