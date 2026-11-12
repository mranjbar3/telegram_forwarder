from datetime import datetime
from pydantic import BaseModel

class SourceCreate(BaseModel):
    chat_id: int
    title: str

class DestinationCreate(BaseModel):
    chat_id: int
    title: str

class RuleCreate(BaseModel):
    name: str
    rule_type: str
    pattern: str
    is_active: bool = True

class MessageOut(BaseModel):
    id: int
    source_chat_title: str
    dest_chat_title: str
    status: str
    retry_count: int
    error_message: str
    content_preview: str
    created_at: datetime
    class Config:
        from_attributes = True
