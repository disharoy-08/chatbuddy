import os
import logging
from collections.abc import Generator
from typing import Optional
from dotenv import load_dotenv
from fastapi import HTTPException, status
from google import genai
from google.genai import errors, types

load_dotenv()
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Conversation, Message, MessageRole
from schemas import ChatRequest



# 1. Accept a validated ChatRequest.
# 2.Verify the conversation exists in PostgreSQL.
# 3.Save the user's message.
# 4.Retrieve the latest 10 messages for that conversation.
# 5.Send the ordered history to Gemini.
# 6.Stream the generated response and save the completed assistant message.

logger = logging.getLogger("uvicorn.error")

# Initialize Gemini Client (reads GEMINI_API_KEY from environment)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Configurable sliding-window context limit (default: 10)
CONTEXT_LIMIT = int(os.getenv("CONTEXT_WINDOW_LIMIT", 10))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")  


def get_or_create_conversation(db: Session, conversation_id: Optional[int], first_message: str) -> Conversation:
    """Retrieves existing conversation or creates a new one with a dynamic title."""
    
    if conversation_id is not None:
        conversation = db.get(Conversation, conversation_id)
        if conversation:
            return conversation
        
    # If conversation_id is None, create a brand-new conversation!
    title = (first_message[:30] + "...") if len(first_message) > 30 else first_message
    new_conversation = Conversation(title=title or "New Chat")
    
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)  
    
    return new_conversation


def get_conversation_history(db: Session, conversation_id: int, limit: int = CONTEXT_LIMIT) -> list[Message]:
    """Fetches the last N messages in chronological order for LLM context."""
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )
    # Reverse so the oldest of the last N turns comes first
    recent_messages = list(db.scalars(stmt).all())
    recent_messages.reverse()
    return recent_messages


def _build_gemini_contents(history: list[Message], new_message: str) -> list[types.ContentUnionDict]:
    """Helper to convert DB history and current prompt into Gemini Content objects."""
    contents: list[types.ContentUnionDict] = []
    for msg in history:
        role = "user" if msg.role == MessageRole.user else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            )
        )
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=new_message)]
        )
    )
    return contents


def process_chat(db: Session, chat_request: ChatRequest) -> dict:
    
    conversation = get_or_create_conversation(db, chat_request.conversation_id, chat_request.message)
    history_messages = get_conversation_history(db, conversation.id)
    
    # Save user message
    user_msg = Message(conversation_id=conversation.id, role=MessageRole.user, content=chat_request.message)
    db.add(user_msg)
    db.commit()
    
    gemini_contents = _build_gemini_contents(history_messages, chat_request.message)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=gemini_contents,
        )
        assistant_reply = response.text or "No response generated."
        
    except errors.APIError as e:
        logger.error(f"Gemini API Error: {e}")
        # Standard HTTP error with readable JSON body
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "AI_SERVICE_ERROR",
                "message": f"Gemini API Error: {e.message}",
            }
        )
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while generating response.",
            }
        )
        
    # Save assistant response
    assistant_msg = Message(conversation_id=conversation.id, role=MessageRole.assistant, content=assistant_reply)
    db.add(assistant_msg)
    db.commit()
    return {
        "conversation_id": conversation.id,
        "user_message": chat_request.message,
        "assistant_response": assistant_reply,
    }


from database import SessionLocal


def ensure_conversation(conversation_id: Optional[int], first_message: str) -> int:
    """Ensures conversation exists in its own scoped session and returns the conversation ID."""
    with SessionLocal() as db:
        conv = get_or_create_conversation(db, conversation_id, first_message)
        return conv.id


def process_chat_stream(chat_request: ChatRequest) -> Generator[str, None, None]:
    """Streams Gemini response tokens safely without holding or exhausting database connections."""
    
    # 1. Read context and persist user message in a short-lived scoped session
    with SessionLocal() as db:
        conversation = get_or_create_conversation(db, chat_request.conversation_id, chat_request.message)
        chat_request.conversation_id = conversation.id
        
        history_messages = get_conversation_history(db, conversation.id)
        
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.user,
            content=chat_request.message,
        )
        db.add(user_message)
        db.commit()
        
        gemini_contents = _build_gemini_contents(history_messages, chat_request.message)
        conv_id = conversation.id

    # 2. Stream tokens from Gemini (Zero DB locks held during streaming!)
    accumulated_response: list[str] = []

    try:
        response_stream = client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=gemini_contents,
        )
        for chunk in response_stream:
            if chunk.text:
                accumulated_response.append(chunk.text)
                yield chunk.text
                
    except errors.APIError as e:
        logger.error(f"Gemini Streaming Error: {e}")
        yield f"\n\n[Error: Gemini AI service failed: {e.message}]"
        return
    except Exception as e:
        logger.error(f"Unexpected Streaming Error: {e}")
        yield "\n\n[Error: An unexpected error occurred while streaming response.]"
        return

    # 3. Once stream completes, persist the complete assistant response in a new clean session
    full_text = "".join(accumulated_response)
    if full_text:
        with SessionLocal() as db:
            assistant_message = Message(
                conversation_id=conv_id,
                role=MessageRole.assistant,
                content=full_text,
            )
            db.add(assistant_message)
            db.commit()


    
