# backend/app/models/email_analysis.py
"""
Email Analysis Models
Pydantic models for email response analysis and classification
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .application import ApplicationStatus


class EmailResponseCategory(str, Enum):
    """Categories for email response classification"""
    INTERVIEW_INVITATION = "interview_invitation"
    REJECTION = "rejection"
    OFFER = "offer"
    INFORMATION_REQUEST = "information_request"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    ACKNOWLEDGMENT = "acknowledgment"
    SCHEDULING_REQUEST = "scheduling_request"
    UNKNOWN = "unknown"


class EmailAnalysisResult(BaseModel):
    """Result of email analysis"""
    category: EmailResponseCategory
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    suggested_status: Optional[ApplicationStatus] = None
    requires_action: bool = False
    action_type: Optional[str] = None  # "create_task", "create_reminder", "update_status"
    action_details: Dict[str, Any] = {}
    keywords_matched: List[str] = []
    ai_reasoning: Optional[str] = None
    ai_used: bool = False
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Extracted information
    extracted_info: Dict[str, Any] = {}  # dates, times, requirements, etc.
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ApplicationUpdateResult(BaseModel):
    """Result of updating application based on email analysis"""
    success: bool
    application_id: str
    old_status: Optional[ApplicationStatus] = None
    new_status: Optional[ApplicationStatus] = None
    actions_taken: List[str] = []
    timeline_event_created: bool = False
    notification_sent: bool = False
    task_created: bool = False
    reminder_created: bool = False
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AnalyzeEmailRequest(BaseModel):
    """Request model for analyzing an email"""
    email_content: str
    email_subject: str
    sender_email: str
    application_id: Optional[str] = None
    use_ai: bool = True


class EmailResponseData(BaseModel):
    """Email response data for processing"""
    email_content: str
    email_subject: str
    sender_email: str
    received_at: Optional[datetime] = None
    email_id: Optional[str] = None
    thread_id: Optional[str] = None


# Export all models
__all__ = [
    "EmailResponseCategory",
    "EmailAnalysisResult",
    "ApplicationUpdateResult",
    "AnalyzeEmailRequest",
    "EmailResponseData"
]
