from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DebateBase(BaseModel):
    topic: str
    rounds: int
    messages: str  # JSON 문자열
    retrieved_docs: Optional[str] = None  # JSON 문자열


class DebateCreate(DebateBase):
    pass


class DebateUpdate(BaseModel):
    topic: Optional[str] = None
    rounds: Optional[int] = None
    messages: Optional[str] = None
    retrieved_docs: Optional[str] = None


class DebateSchema(DebateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
