# backend/app/models/__init__.py
"""
Pydantic models package for the AI Job Application Platform
"""

from .common import *
from .user import *
from .job import *
from .application import *
from .subscription import *
from .email_analysis import *


__all__ = [
    # Common models
    "BaseModel",
    "BaseResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "FileUploadResponse",
    
    # User models
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "LocationPreference",
    "JobPreferences",
    "PersonalInfo",
    "UserUsageStats",
    "UserPreferences",
    "PasswordReset",
    "PasswordChange",
    "PasswordResetConfirm",
    "TokenResponse",
    "RefreshTokenRequest",
    "SubscriptionTier",
    "UserRole",
    
    # Job models
    "Job",
    "JobCreate",
    "JobUpdate",
    "JobResponse",
    "JobSearch",
    "JobFilter",
    "JobMatch",
    "JobSource",
    "JobStatus",
    "JobRequirement",
    "JobBenefit",
    "SalaryRange",
    "CompanyInfo",
    "JobListResponse",
    
    # Application models
    "Application",
    "ApplicationCreate",
    "ApplicationUpdate",
    "ApplicationResponse",
    "ApplicationStatus",
    "ApplicationDocument",
    "ApplicationTracking",
    "ApplicationStats",
    "ApplicationListResponse",
    "CoverLetter",
    "CustomCV",
    
    # Subscription models
    "Subscription",
    "SubscriptionCreate",
    "SubscriptionUpdate",
    "SubscriptionResponse",
    "SubscriptionPlan",
    "SubscriptionStatus",
    "UsageLimit",
    "BillingInfo",
    "PaymentMethod",
    "Invoice",
    "SubscriptionStats",
    
    # Email Analysis models
    "EmailResponseCategory",
    "EmailAnalysisResult",
    "ApplicationUpdateResult",
    "AnalyzeEmailRequest",
    "EmailResponseData",
]