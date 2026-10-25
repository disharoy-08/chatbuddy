from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import ChatRequest
from services import chat_service
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(chat_request: ChatRequest, db: Session = Depends(get_db)):
       """Handles chat message: persists to DB, fetches context, calls Gemini, returns response."""
       return chat_service.process_chat(db, chat_request)
   
   
   
@router.post("/stream")
def chat_stream(chat_request: ChatRequest):
    """Streams response chunks in real-time as Server-Sent Events / text stream."""
    # Ensure conversation exists to extract ID for response header
    conv_id = chat_service.ensure_conversation(
        chat_request.conversation_id, chat_request.message
    )
    chat_request.conversation_id = conv_id
    
    return StreamingResponse(
        chat_service.process_chat_stream(chat_request),
        media_type="text/plain",
        headers={"X-Conversation-Id": str(conv_id)}
    )

