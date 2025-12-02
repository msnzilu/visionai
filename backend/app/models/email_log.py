# backend/app/models/email_log.py
"""
Email Log Pydantic models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .common import TimeStampedModel

class EmailDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class EmailStatus(str, Enum):
    SENT = "sent"
    RECEIVED = "received"
    FAILED = "failed"
    DRAFT = "draft"

class EmailLog(TimeStampedModel):
    """Log of emails sent/received by the agent"""
    id: Optional[str] = Field(alias="_id")
    user_id: str
    application_id: Optional[str] = None
    job_id: Optional[str] = None
    
    direction: EmailDirection
    status: EmailStatus
    
    message_id: str
    thread_id: str
    
    sender: str
    recipient: str
    subject: Optional[str] = None
    snippet: Optional[str] = None
    
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    sent_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
