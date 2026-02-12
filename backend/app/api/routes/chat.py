import logging
import subprocess

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import handle_chat_message
from app.services.claude import ClaudeError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI chat with video knowledge context."""
    try:
        return handle_chat_message(request.message, request.conversation_id)
    except ClaudeError as e:
        logger.error(f"Claude error in chat: {e}")
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable")
    except subprocess.TimeoutExpired:
        logger.error("Claude request timed out")
        raise HTTPException(status_code=504, detail="AI response timed out")
