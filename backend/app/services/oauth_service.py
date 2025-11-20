# backend/app/services/oauth_service.py
"""
OAuth service for Google and LinkedIn authentication
Save this file in: backend/app/services/oauth_service.py
"""

import secrets
import httpx
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

from app.config import settings
from app.database import get_users_collection
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication"""
    
    # In-memory storage for OAuth state tokens (simple approach)
    # For production, use Redis or database
    _state_tokens = {}
    
    @staticmethod
    def generate_state_token() -> str:
        """Generate OAuth state token"""
        state = secrets.token_urlsafe(32)
        OAuthService._state_tokens[state] = datetime.utcnow()
        return state
    
    @staticmethod
    def verify_state_token(state: str) -> bool:
        """Verify OAuth state token"""
        if state in OAuthService._state_tokens:
            # Remove token after use (one-time use)
            del OAuthService._state_tokens[state]
            return True
        return False
    
    # ============ GOOGLE OAUTH ============
    
    @staticmethod
    def get_google_auth_url() -> Tuple[str, str]:
        """Generate Google OAuth authorization URL"""
        state = OAuthService.generate_state_token()
        
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
            "prompt": "select_account"
        }
        
        from urllib.parse import urlencode
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state
    
    @staticmethod
    async def exchange_google_code(code: str) -> Optional[Dict]:
        """Exchange Google authorization code for tokens"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Google token exchange failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error exchanging Google code: {str(e)}")
            return None
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> Optional[Dict]:
        """Get user info from Google"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Google user info failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Google user info: {str(e)}")
            return None
    
    # ============ LINKEDIN OAUTH ============
    
    @staticmethod
    def get_linkedin_auth_url() -> Tuple[str, str]:
        """Generate LinkedIn OAuth authorization URL"""
        state = OAuthService.generate_state_token()
        
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "state": state,
            "scope": "openid profile email"
        }
        
        from urllib.parse import urlencode
        auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
        return auth_url, state
    
    @staticmethod
    async def exchange_linkedin_code(code: str) -> Optional[Dict]:
        """Exchange LinkedIn authorization code for tokens"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.linkedin.com/oauth/v2/accessToken",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": settings.LINKEDIN_CLIENT_ID,
                        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                        "redirect_uri": settings.LINKEDIN_REDIRECT_URI
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"LinkedIn token exchange failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error exchanging LinkedIn code: {str(e)}")
            return None
    
    @staticmethod
    async def get_linkedin_user_info(access_token: str) -> Optional[Dict]:
        """Get user info from LinkedIn"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.linkedin.com/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"LinkedIn user info failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting LinkedIn user info: {str(e)}")
            return None
    
    # ============ USER HANDLING ============
    
    @staticmethod
    async def handle_oauth_user(
        email: str,
        first_name: str,
        last_name: str,
        oauth_provider: str,
        oauth_id: str
    ) -> Tuple[Dict, str, bool]:
        """
        Handle OAuth user - create or login
        Returns: (user, token, is_new_user)
        """
        users_collection = await get_users_collection()
        
        # Check if user exists
        user = await users_collection.find_one({"email": email})
        is_new_user = False
        
        if user:
            # Update OAuth info and last login
            await users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        f"oauth.{oauth_provider}": {
                            "id": oauth_id,
                            "connected_at": datetime.utcnow()
                        },
                        "last_login": datetime.utcnow(),
                        "is_verified": True
                    }
                }
            )
            user = await users_collection.find_one({"_id": user["_id"]})
        else:
            # Create new user
            is_new_user = True
            
            # Generate unique referral code
            import random
            import string
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            user_doc = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "password": None,  # OAuth users don't have password initially
                "is_active": True,
                "is_verified": True,
                "verified_at": datetime.utcnow(),
                "role": "user",
                "subscription_tier": "free",
                "oauth": {
                    oauth_provider: {
                        "id": oauth_id,
                        "connected_at": datetime.utcnow()
                    }
                },
                "referral_code": referral_code,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "usage_stats": {
                    "total_searches": 0,
                    "total_applications": 0,
                    "monthly_searches": 0
                }
            }
            
            result = await users_collection.insert_one(user_doc)
            user = await users_collection.find_one({"_id": result.inserted_id})
        
        # Create access token using your existing auth service
        from app.core.security import create_access_token
        token = create_access_token(str(user["_id"]))
        
        return user, token, is_new_user