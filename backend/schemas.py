from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Chat(BaseModel):
    session_id: str = Field(..., description="Client-provided session identifier")
    title: Optional[str] = Field(None, description="Optional title for the chat session")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Chatmessage(BaseModel):
    session_id: str
    role: str = Field(..., description="user or assistant")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Research(BaseModel):
    session_id: str
    topic: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Planitem(BaseModel):
    session_id: str
    day: str
    tasks: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Plan(BaseModel):
    session_id: str
    week_start: date
    items: List[Planitem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Roleplay(BaseModel):
    session_id: str
    persona: str
    instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
