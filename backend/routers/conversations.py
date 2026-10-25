from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Conversation, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
def list_conversations(db: Session = Depends(get_db)):
    """List all conversations ordered by creation date (newest first)."""
    stmt = select(Conversation).order_by(Conversation.created_at.desc())
    conversations = db.scalars(stmt).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in conversations
    ]


@router.get("/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    """Retrieve full chronological message history for a specific conversation."""
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = db.scalars(stmt).all()
    return [
        {
            "id": m.id,
            "role": m.role.value if hasattr(m.role, "value") else str(m.role),
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a conversation and all its associated messages."""
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"message": f"Conversation {conversation_id} deleted successfully"}
