# backend/app/models/notification.py
"""
Notification models for Phase 5
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications"""
    APPLICATION_SUBMITTED = "application_submitted"
    STATUS_UPDATE = "status_update"
    INTERVIEW_REMINDER = "interview_reminder"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    DEADLINE_REMINDER = "deadline_reminder"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_REPORT = "monthly_report"
    TEST = "test"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    PUSH = "push"


class NotificationBase(BaseModel):
    """Base notification model"""
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])


class NotificationCreate(NotificationBase):
    """Create notification request"""
    pass


class Notification(NotificationBase):
    """Complete notification model"""
    id: Optional[str] = Field(None, alias="_id")
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    data: Dict[str, Any] = {}
    channels: List[str] = []
    is_read: bool
    created_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UnreadCountResponse(BaseModel):
    """Unread notification count"""
    unread_count: int


class MarkAsReadRequest(BaseModel):
    """Mark notification as read request"""
    notification_id: str


class BulkMarkAsReadRequest(BaseModel):
    """Bulk mark as read request"""
    notification_ids: List[str]