# backend/app/dependencies.py
"""
FastAPI Dependencies
Common dependencies used across the application
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from app.core.security import verify_access_token, verify_refresh_token
from app.database import (
    get_users_collection, 
    get_subscriptions_collection,
    get_usage_tracking_collection
)
from app.models.user import SubscriptionTier
from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token"""
    if not credentials:
        logger.debug("No credentials provided")
        return None
    
    try:
        from bson import ObjectId
        
        payload = verify_access_token(credentials.credentials)
        logger.debug(f"Token payload: {payload}")
        
        if not payload:
            logger.debug("Payload is None")
            return None
        
        user_id = payload.get("sub")
        logger.debug(f"User ID from token: {user_id}")
        
        if not user_id:
            logger.debug("No user_id in payload")
            return None
        
        try:
            user_object_id = ObjectId(user_id)
        except Exception as e:
            logger.error(f"Failed to convert to ObjectId: {e}")
            return None
        
        users_collection = await get_users_collection()
        user = await users_collection.find_one({"_id": user_object_id})
        
        if user:
            logger.debug(f"Found user: {user.get('email')}")
        else:
            logger.debug("User not found in database")
        
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None


async def get_current_active_user(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current active user (required authentication)
    Raises HTTPException if user not authenticated or inactive
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


async def get_current_verified_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current verified user (email verification required)
    """
    if not current_user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification required"
        )
    
    return current_user


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current admin user (admin role required)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


# Subscription Dependencies
async def get_user_subscription(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get user's current subscription details
    """
    subscriptions_collection = await get_subscriptions_collection()
    subscription = await subscriptions_collection.find_one({
        "user_id": str(current_user["_id"])
    })
    
    if not subscription:
        # Create default free subscription
        subscription = {
            "user_id": str(current_user["_id"]),
            "tier": SubscriptionTier.FREE,
            "status": "active",
            "created_at": datetime.utcnow(),
            "expires_at": None,
            "usage_limits": {
                "monthly_attempts": settings.FREE_TIER_MONTHLY_ATTEMPTS,
                "jobs_per_attempt": settings.FREE_TIER_JOBS_PER_ATTEMPT,
                "daily_attempts": 0
            },
            "current_usage": {
                "monthly_attempts": 0,
                "daily_attempts": 0,
                "last_reset": datetime.utcnow()
            }
        }
        result = await subscriptions_collection.insert_one(subscription)
        subscription["_id"] = result.inserted_id
    
    return subscription


async def check_subscription_limits(
    action: str = "search",  # search, apply, generate_cv, generate_cover_letter
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    subscription: Dict[str, Any] = Depends(get_user_subscription)
) -> Dict[str, Any]:
    """
    Check if user can perform the requested action based on subscription limits
    """
    # Reset counters if needed
    subscription = await reset_usage_counters_if_needed(subscription)
    
    tier = subscription.get("tier", SubscriptionTier.FREE)
    current_usage = subscription.get("current_usage", {})
    usage_limits = subscription.get("usage_limits", {})
    
    # Check limits based on action and tier
    if action == "search":
        monthly_limit = usage_limits.get("monthly_attempts", 0)
        daily_limit = usage_limits.get("daily_attempts", 0)
        
        monthly_used = current_usage.get("monthly_attempts", 0)
        daily_used = current_usage.get("daily_attempts", 0)
        
        if monthly_limit > 0 and monthly_used >= monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly search limit reached. Upgrade your plan for more searches."
            )
        
        if daily_limit > 0 and daily_used >= daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily search limit reached. Try again tomorrow or upgrade your plan."
            )
    
    return subscription


async def reset_usage_counters_if_needed(subscription: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reset usage counters if period has passed
    """
    current_usage = subscription.get("current_usage", {})
    last_reset = current_usage.get("last_reset", datetime.utcnow())
    now = datetime.utcnow()
    
    # Reset daily counters
    if now.date() > last_reset.date():
        current_usage["daily_attempts"] = 0
    
    # Reset monthly counters
    if now.month != last_reset.month or now.year != last_reset.year:
        current_usage["monthly_attempts"] = 0
    
    # Update last reset time
    current_usage["last_reset"] = now
    subscription["current_usage"] = current_usage
    
    # Update in database
    subscriptions_collection = await get_subscriptions_collection()
    await subscriptions_collection.update_one(
        {"_id": subscription["_id"]},
        {"$set": {"current_usage": current_usage}}
    )
    
    return subscription


async def increment_usage(
    action: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    subscription: Dict[str, Any] = Depends(get_user_subscription)
) -> None:
    """
    Increment usage counters for the specified action
    """
    current_usage = subscription.get("current_usage", {})
    
    if action == "search":
        current_usage["monthly_attempts"] = current_usage.get("monthly_attempts", 0) + 1
        current_usage["daily_attempts"] = current_usage.get("daily_attempts", 0) + 1
    
    # Update in database
    subscriptions_collection = await get_subscriptions_collection()
    await subscriptions_collection.update_one(
        {"_id": subscription["_id"]},
        {"$set": {"current_usage": current_usage}}
    )
    
    # Log usage for analytics
    await log_usage_event(str(current_user["_id"]), action)


async def log_usage_event(user_id: str, action: str, metadata: Optional[Dict] = None) -> None:
    """
    Log usage event for analytics and monitoring
    """
    try:
        usage_collection = await get_usage_tracking_collection()
        usage_event = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        await usage_collection.insert_one(usage_event)
    except Exception as e:
        logger.error(f"Failed to log usage event: {str(e)}")


# Pagination Dependencies
class PaginationParams:
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ):
        self.page = max(1, page)
        self.size = min(max(1, size), max_size)
        self.skip = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> PaginationParams:
    """
    Get pagination parameters with validation
    """
    return PaginationParams(page=page, size=size)


# File Upload Dependencies
def validate_file_upload(
    max_size: int = settings.MAX_FILE_SIZE,
    allowed_types: list = None
):
    """
    Dependency factory for file upload validation
    """
    if allowed_types is None:
        allowed_types = settings.ALLOWED_FILE_TYPES
    
    def _validate_file(file):
        if file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {max_size / (1024*1024):.1f}MB"
            )
        
        # Check file extension
        file_extension = "." + file.filename.split(".")[-1].lower()
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )
        
        return file
    
    return _validate_file


# Rate Limiting Dependencies
class RateLimiter:
    def __init__(self, requests: int = 100, period: int = 3600):
        self.requests = requests
        self.period = period
        self.requests_cache = {}
    
    async def __call__(self, request: Request):
        client_ip = request.client.host
        current_time = datetime.utcnow()
        
        # Clean old entries
        cutoff_time = current_time - timedelta(seconds=self.period)
        self.requests_cache = {
            ip: timestamps for ip, timestamps in self.requests_cache.items()
            if timestamps and timestamps[-1] > cutoff_time
        }
        
        # Check current IP
        if client_ip in self.requests_cache:
            # Filter timestamps within the period
            recent_requests = [
                timestamp for timestamp in self.requests_cache[client_ip]
                if timestamp > cutoff_time
            ]
            
            if len(recent_requests) >= self.requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later."
                )
            
            recent_requests.append(current_time)
            self.requests_cache[client_ip] = recent_requests
        else:
            self.requests_cache[client_ip] = [current_time]


# API Key Dependencies (for external integrations)
async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = None
) -> bool:
    """
    Verify API key for external integrations
    """
    api_key = x_api_key or request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # In production, validate against database of valid API keys
    # For now, check against a simple setting
    valid_keys = [settings.BROWSER_AUTOMATION_TOKEN, settings.WEBHOOK_SECRET]
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True


# Content Type Dependencies
def require_json_content_type(request: Request):
    """
    Ensure request has JSON content type
    """
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content-Type must be application/json"
        )


# Create rate limiter instances
api_rate_limiter = RateLimiter(requests=settings.RATE_LIMIT_REQUESTS, period=settings.RATE_LIMIT_PERIOD)
auth_rate_limiter = RateLimiter(requests=10, period=900)  # 10 requests per 15 minutes for auth endpoints