# backend/app/api/auth.py
"""
CVision Authentication API - Frontend Compatible
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from bson import ObjectId
from fastapi.responses import RedirectResponse
from app.services.oauth_service import OAuthService
from app.config import settings
from app.database import get_users_collection

import logging
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None  # Added for frontend compatibility
    subscription_tier: str
    created_at: str


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# Utility functions
def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    payload = {
        'sub': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> str:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get('sub')
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(token: str = Depends(security)):
    """Get current user from token"""
    user_id = verify_token(token.credentials)
    users_collection = await get_users_collection()
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# API Routes
@router.post("/register", response_model=APIResponse)
async def register(user_data: UserRegister):
    """Register new user in CVision"""
    try:
        users_collection = await get_users_collection()
        
        # Check if user exists
        existing_user = await users_collection.find_one({"email": user_data.email})
        if existing_user:
            return APIResponse(
                success=False,
                message="Email already registered"
            )
        
        # Generate unique referral code
        def generate_unique_referral_code():
            import random
            import string
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Ensure referral code is unique
        referral_code = None
        max_attempts = 5
        for attempt in range(max_attempts):
            temp_code = generate_unique_referral_code()
            existing_referral = await users_collection.find_one({"referral_code": temp_code})
            if not existing_referral:
                referral_code = temp_code
                break
        
        # If we couldn't generate a unique code, leave it as None (will be handled by partial index)
        if not referral_code:
            print("Warning: Could not generate unique referral code after 5 attempts")
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "password": hash_password(user_data.password),
            "first_name": user_data.first_name or "",
            "last_name": user_data.last_name or "",
            "referral_code": referral_code,  # This can be None if generation failed
            "subscription_tier": "free",
            "is_active": True,
            "is_verified": True,  # Simplified for testing
            "created_at": datetime.utcnow(),
            "usage_stats": {
                "monthly_searches": 0,
                "total_applications": 0
            }
        }
        
        result = await users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        # Create token
        token = create_access_token(str(result.inserted_id))
        
        # Create full_name for frontend compatibility
        full_name = f"{user_doc['first_name']} {user_doc['last_name']}".strip()
        if not full_name:
            full_name = user_doc["email"].split("@")[0]  # Fallback to email prefix
        
        user_response = {
            "id": str(user_doc["_id"]),
            "email": user_doc["email"],
            "first_name": user_doc["first_name"],
            "last_name": user_doc["last_name"],
            "full_name": full_name,
            "referral_code": user_doc["referral_code"],  # Include referral code in response
            "subscription_tier": user_doc["subscription_tier"],
            "created_at": user_doc["created_at"].isoformat()
        }
        
        return APIResponse(
            success=True,
            message="User registered successfully",
            data={
                "access_token": token,
                "token_type": "bearer",
                "user": user_response
            }
        )
        
    except Exception as e:
        # Handle specific MongoDB duplicate key errors
        if "E11000" in str(e) and "referral_code" in str(e):
            return APIResponse(
                success=False,
                message="Registration temporarily unavailable. Please try again."
            )
        elif "E11000" in str(e) and "email" in str(e):
            return APIResponse(
                success=False,
                message="Email already registered"
            )
        else:
            # Log the full error for debugging but return user-friendly message
            print(f"Registration error: {str(e)}")
            return APIResponse(
                success=False,
                message="Registration failed. Please try again."
            )


@router.post("/login", response_model=APIResponse)
async def login(login_data: UserLogin):
    """Login to CVision"""
    try:
        users_collection = await get_users_collection()
        
        # Find user
        user = await users_collection.find_one({"email": login_data.email})
        if not user or not verify_password(login_data.password, user["password"]):
            return APIResponse(
                success=False,
                message="Invalid email or password"
            )
        
        # Create token
        token = create_access_token(str(user["_id"]))
        
        # Create full_name for frontend compatibility
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        if not full_name:
            full_name = user["email"].split("@")[0]  # Fallback to email prefix
        
        user_response = {
            "id": str(user["_id"]),
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "full_name": full_name,
            "role": user.get("role", "user"),
            "subscription_tier": user["subscription_tier"],
            "created_at": user["created_at"].isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Login successful",
            data={
                "access_token": token,
                "token_type": "bearer",
                "user": user_response
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Login failed: {str(e)}"
        )


@router.post("/logout", response_model=APIResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user"""
    return APIResponse(
        success=True,
        message="Logged out successfully"
    )


@router.get("/me", response_model=APIResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    try:
        # Create full_name for frontend compatibility
        full_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        if not full_name:
            full_name = current_user["email"].split("@")[0]  # Fallback to email prefix
        
        user_response = {
            "id": str(current_user["_id"]),
            "email": current_user["email"],
            "first_name": current_user.get("first_name", ""),
            "last_name": current_user.get("last_name", ""),
            "full_name": full_name,
            "subscription_tier": current_user["subscription_tier"],
            "created_at": current_user["created_at"].isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Profile retrieved successfully",
            data={"user": user_response}
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to retrieve profile: {str(e)}"
        )

# ============ GOOGLE OAUTH ROUTES ============

@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth flow"""
    try:
        auth_url, state = OAuthService.get_google_auth_url()
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Google login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Google login")


@router.get("/google/callback")
async def google_callback(code: str, state: str):
    """Handle Google OAuth callback"""
    try:
        if not OAuthService.verify_state_token(state):
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=invalid_state")
        
        tokens = await OAuthService.exchange_google_code(code)
        if not tokens:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=token_failed")
        
        user_info = await OAuthService.get_google_user_info(tokens["access_token"])
        if not user_info:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=user_info_failed")
        
        user, token, is_new = await OAuthService.handle_oauth_user(
            email=user_info["email"],
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            oauth_provider="google",
            oauth_id=user_info["id"]
        )
        
        redirect_url = f"{settings.FRONTEND_URL}/auth-callback.html?token={token}&provider=google"
        if is_new:
            redirect_url += "&new_user=true"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=auth_failed")


# ============ LINKEDIN OAUTH ROUTES ============

@router.get("/linkedin/login")
async def linkedin_login():
    """Initiate LinkedIn OAuth flow"""
    try:
        auth_url, state = OAuthService.get_linkedin_auth_url()
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"LinkedIn login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate LinkedIn login")


@router.get("/linkedin/callback")
async def linkedin_callback(code: str, state: str):
    """Handle LinkedIn OAuth callback"""
    try:
        if not OAuthService.verify_state_token(state):
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=invalid_state")
        
        tokens = await OAuthService.exchange_linkedin_code(code)
        if not tokens:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=token_failed")
        
        user_info = await OAuthService.get_linkedin_user_info(tokens["access_token"])
        if not user_info:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=user_info_failed")
        
        user, token, is_new = await OAuthService.handle_oauth_user(
            email=user_info["email"],
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            oauth_provider="linkedin",
            oauth_id=user_info["sub"]
        )
        
        redirect_url = f"{settings.FRONTEND_URL}/auth-callback.html?token={token}&provider=linkedin"
        if is_new:
            redirect_url += "&new_user=true"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"LinkedIn callback error: {str(e)}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login.html?error=auth_failed")