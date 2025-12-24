
"""
Security Service for business logic security checks
"""
from typing import Optional
import logging
from app.database import get_users_collection

logger = logging.getLogger(__name__)

class SecurityService:
    """Service for handling security-related business logic"""

    @classmethod
    async def check_registration_ip_limit(cls, ip_address: str, limit: int = 3) -> bool:
        """
        Check if the given IP address has reached the registration limit.
        Returns True if registration is allowed, False if limit is reached.
        """
        if not ip_address:
            # If no IP is provided (shouldn't happen with get_client_ip), allow it but log warning
            logger.warning("Registration check called without IP address")
            return True
            
        users_collection = await get_users_collection()
        
        # Increase limit for local development / Docker gateway
        if ip_address in ["127.0.0.1", "::1", "172.18.0.1"] or ip_address.startswith("172."):
            limit = 50
            
        count = await users_collection.count_documents({"registration_ip": ip_address})
        
        if count >= limit:
            logger.warning(f"Registration limit reached for IP {ip_address}: {count}/{limit}")
            return False
        
        return True
