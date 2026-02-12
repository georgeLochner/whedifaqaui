import logging
import subprocess
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.document import DocumentDetail, DocumentRequest, DocumentResponse
from app.services.claude import ClaudeError
from app.services.document import generate_document, get_document

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    request: DocumentRequest, db: Session = Depends(get_db)
):
    """Generate a summary document from video transcripts."""
    try:
        doc = generate_document(request, session_id=None, db=db)
        return DocumentResponse(
            id=doc.id,
            title=doc.title,
            preview=doc.content[:100],
            source_count=len(doc.source_video_ids) if doc.source_video_ids else 0,
            created_at=doc.created_at,
        )
    except ClaudeError as e:
        logger.error(f"Claude error in document generation: {e}")
        raise HTTPException(
            status_code=500, detail="AI service temporarily unavailable"
        )
    except subprocess.TimeoutExpired:
        logger.error("Claude request timed out during document generation")
        raise HTTPException(status_code=504, detail="AI response timed out")
    except Exception as e:
        logger.error(f"Unexpected error in document generation: {e}")
        raise HTTPException(
            status_code=500, detail="AI service temporarily unavailable"
        )


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def retrieve_document(
    document_id: UUID, db: Session = Depends(get_db)
):
    """Retrieve a generated document by ID."""
    doc = get_document(document_id, db)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetail(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        source_video_ids=doc.source_video_ids or [],
        created_at=doc.created_at,
    )


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: UUID, db: Session = Depends(get_db)
):
    """Download a generated document as a markdown file."""
    doc = get_document(document_id, db)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = f"{doc.title[:50].replace(' ', '_')}.md"
    return Response(
        content=doc.content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
