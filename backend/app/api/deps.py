# backend/app/api/deps.py
"""
API-specific dependencies for FastAPI routes
"""

from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, Generator
from bson import ObjectId
import logging

from app.dependencies import (
    get_current_user, get_current_active_user, get_current_verified_user,
    get_current_admin_user, get_user_subscription, check_subscription_limits,
    increment_usage, PaginationParams, get_pagination_params
)
from app.core.security import verify_access_token
from app.database import get_database
from app.models.user import User, SubscriptionTier
from app.models.subscription import Subscription
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Re-export common dependencies for convenience
CurrentUser = Depends(get_current_user)
CurrentActiveUser = Depends(get_current_active_user)
CurrentVerifiedUser = Depends(get_current_verified_user)
CurrentAdminUser = Depends(get_current_admin_user)
UserSubscription = Depends(get_user_subscription)
PaginationDep = Depends(get_pagination_params)


# API-specific dependencies
async def get_valid_object_id(
    id: str,
    field_name: str = "id"
) -> ObjectId:
    """
    Validate and convert string ID to ObjectId
    """
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format"
        )


async def get_user_by_id(
    user_id: str,
    current_user: Dict[str, Any] = CurrentActiveUser
) -> Dict[str, Any]:
    """
    Get user by ID with permission checking
    """
    # Convert and validate user_id
    try:
        target_user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Check permissions (users can only access their own data, admins can access any)
    current_user_id = ObjectId(current_user["_id"])
    if current_user_id != target_user_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's data"
        )
    
    # Get target user
    target_user = await AuthService.get_user_by_id(str(target_user_id))
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return target_user


async def check_user_ownership(
    resource_user_id: str,
    current_user: Dict[str, Any] = CurrentActiveUser
) -> bool:
    """
    Check if current user owns the resource or is admin
    """
    current_user_id = str(current_user["_id"])
    is_admin = current_user.get("role") == "admin"
    
    if current_user_id != resource_user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    
    return True


async def validate_subscription_access(
    required_tier: SubscriptionTier,
    current_user: Dict[str, Any] = CurrentActiveUser,
    subscription: Dict[str, Any] = UserSubscription
) -> Dict[str, Any]:
    """
    Validate user has required subscription tier
    """
    user_tier = SubscriptionTier(subscription.get("tier", "free"))
    
    # Define tier hierarchy
    tier_hierarchy = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.BASIC: 1,
        SubscriptionTier.PREMIUM: 2
    }
    
    if tier_hierarchy[user_tier] < tier_hierarchy[required_tier]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires {required_tier.value} subscription or higher"
        )
    
    return subscription


async def check_feature_access(
    feature_name: str,
    current_user: Dict[str, Any] = CurrentActiveUser,
    subscription: Dict[str, Any] = UserSubscription
) -> bool:
    """
    Check if user has access to specific feature
    """
    user_tier = subscription.get("tier", "free")
    
    # Define feature access by tier
    feature_access = {
        "free": [
            "basic_job_search", "basic_cv_upload", "basic_applications"
        ],
        "basic": [
            "basic_job_search", "basic_cv_upload", "basic_applications",
            "cv_customization", "cover_letter_generation", "advanced_search",
            "application_tracking", "basic_analytics"
        ],
        "premium": [
            "basic_job_search", "basic_cv_upload", "basic_applications",
            "cv_customization", "cover_letter_generation", "advanced_search",
            "application_tracking", "basic_analytics", "auto_application",
            "advanced_analytics", "priority_support", "bulk_operations",
            "api_access", "interview_prep", "salary_insights"
        ]
    }
    
    if feature_name not in feature_access.get(user_tier, []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Feature '{feature_name}' not available in your subscription plan"
        )
    
    return True


async def rate_limit_check(
    request: Request,
    action: str = "general",
    current_user: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Check rate limits for API actions
    """
    from app.core.security import rate_limiter
    
    # Use user ID if available, otherwise use IP
    if current_user:
        key = f"user:{current_user['_id']}:{action}"
        # User-based limits (more generous)
        max_attempts = 1000
        window_minutes = 60
    else:
        client_ip = request.client.host
        key = f"ip:{client_ip}:{action}"
        # IP-based limits (more restrictive)
        max_attempts = 100
        window_minutes = 60
    
    if rate_limiter.is_rate_limited(key, max_attempts, window_minutes):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return True


class CommonQueryParams:
    """Common query parameters for list endpoints"""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(20, ge=1, le=100, description="Items per page"),
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
        search: Optional[str] = Query(None, description="Search query"),
        filters: Optional[str] = Query(None, description="JSON filters")
    ):
        self.page = page
        self.size = size
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.search = search
        self.filters = filters


class JobQueryParams(CommonQueryParams):
    """Job-specific query parameters"""
    
    def __init__(
        self,
        location: Optional[str] = Query(None, description="Job location"),
        remote_only: bool = Query(False, description="Remote jobs only"),
        salary_min: Optional[int] = Query(None, ge=0, description="Minimum salary"),
        salary_max: Optional[int] = Query(None, ge=0, description="Maximum salary"),
        employment_type: Optional[str] = Query(None, description="Employment type"),
        experience_level: Optional[str] = Query(None, description="Experience level"),
        company: Optional[str] = Query(None, description="Company name"),
        skills: Optional[str] = Query(None, description="Required skills (comma-separated)"),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.location = location
        self.remote_only = remote_only
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.employment_type = employment_type
        self.experience_level = experience_level
        self.company = company
        self.skills = skills.split(",") if skills else []


class ApplicationQueryParams(CommonQueryParams):
    """Application-specific query parameters"""
    
    def __init__(
        self,
        status: Optional[str] = Query(None, description="Application status"),
        company: Optional[str] = Query(None, description="Company name"),
        priority: Optional[str] = Query(None, description="Priority level"),
        applied_after: Optional[str] = Query(None, description="Applied after date (YYYY-MM-DD)"),
        applied_before: Optional[str] = Query(None, description="Applied before date (YYYY-MM-DD)"),
        has_interviews: Optional[bool] = Query(None, description="Has interviews"),
        needs_follow_up: Optional[bool] = Query(None, description="Needs follow-up"),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.status = status
        self.company = company
        self.priority = priority
        self.applied_after = applied_after
        self.applied_before = applied_before
        self.has_interviews = has_interviews
        self.needs_follow_up = needs_follow_up


# Usage tracking decorators and dependencies
async def track_api_usage(
    action: str,
    current_user: Dict[str, Any],
    subscription: Optional[Dict[str, Any]] = None
):
    """
    Track API usage for analytics and billing
    
    Args:
        action: The action being tracked (e.g., 'get_profile', 'update_profile')
        current_user: The user performing the action (must be a dict, not Depends object)
        subscription: Optional subscription data
    """
    try:
        # Validate that current_user is a dict
        if not isinstance(current_user, dict):
            logger.error(f"track_api_usage received invalid user type: {type(current_user)}")
            return
        
        # Only proceed if we have a valid user ID
        if "_id" not in current_user:
            logger.warning("track_api_usage: user dict missing _id field")
            return
        
        # If subscription not provided, fetch it
        if subscription is None:
            from app.dependencies import get_user_subscription
            try:
                subscription = await get_user_subscription(current_user)
            except Exception as e:
                logger.warning(f"Could not fetch subscription for tracking: {str(e)}")
                subscription = {"tier": "free"}
        
        # Track the usage
        await increment_usage(action, current_user, subscription)
        
    except Exception as e:
        # Don't fail the request if usage tracking fails
        logger.error(f"Failed to track usage for action {action}: {str(e)}", exc_info=True)


# Subscription limit dependencies
async def check_search_limits(
    current_user: Dict[str, Any] = CurrentActiveUser,
    subscription: Dict[str, Any] = UserSubscription
) -> Dict[str, Any]:
    """Check if user can perform job search"""
    return await check_subscription_limits("search", current_user, subscription)


async def check_cv_generation_limits(
    current_user: Dict[str, Any] = CurrentActiveUser,
    subscription: Dict[str, Any] = UserSubscription
) -> Dict[str, Any]:
    """Check if user can generate custom CV"""
    return await check_subscription_limits("cv_generation", current_user, subscription)


async def check_cover_letter_limits(
    current_user: Dict[str, Any] = CurrentActiveUser,
    subscription: Dict[str, Any] = UserSubscription
) -> Dict[str, Any]:
    """Check if user can generate cover letter"""
    return await check_subscription_limits("cover_letter", current_user, subscription)


async def check_auto_apply_limits(
    current_user: Dict[str, Any] = CurrentActiveUser,
    subscription: Dict[str, Any] = UserSubscription
) -> Dict[str, Any]:
    """Check if user can use auto-apply feature"""
    await validate_subscription_access(SubscriptionTier.PREMIUM, current_user, subscription)
    return await check_subscription_limits("auto_apply", current_user, subscription)


# Database session dependency
async def get_db_session():
    """Get database session"""
    db = await get_database()
    try:
        yield db
    finally:
        # MongoDB doesn't need explicit session closing
        pass


# File upload dependencies
def validate_file_upload(
    allowed_types: list = None,
    max_size: int = 10 * 1024 * 1024  # 10MB
):
    """
    Factory for file upload validation dependency
    """
    if allowed_types is None:
        allowed_types = [".pdf", ".docx", ".doc", ".txt"]
    
    async def _validate_file(file):
        if file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {max_size / (1024*1024):.1f}MB"
            )
        
        file_extension = "." + file.filename.split(".")[-1].lower()
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )
        
        return file
    
    return _validate_file


# Admin-only dependency
async def require_admin(current_user: Dict[str, Any] = CurrentActiveUser):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Verification required dependency
async def require_verified_user(current_user: Dict[str, Any] = CurrentVerifiedUser):
    """Require verified user"""
    return current_user

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_db():
    """Get database instance - simple wrapper"""
    from app.database import get_database
    return await get_database()


# Export commonly used dependencies
__all__ = [
    "CurrentUser",
    "CurrentActiveUser", 
    "CurrentVerifiedUser",
    "CurrentAdminUser",
    "UserSubscription",
    "PaginationDep",
    "get_valid_object_id",
    "get_user_by_id",
    "check_user_ownership",
    "validate_subscription_access",
    "check_feature_access",
    "rate_limit_check",
    "CommonQueryParams",
    "JobQueryParams",
    "ApplicationQueryParams",
    "track_api_usage",
    "check_search_limits",
    "check_cv_generation_limits",
    "check_cover_letter_limits",
    "check_auto_apply_limits",
    "get_db_session",
    "validate_file_upload",
    "require_admin",
    "require_verified_user"
]