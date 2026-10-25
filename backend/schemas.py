from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    conversation_id:  Optional[int] = None
    message: str
