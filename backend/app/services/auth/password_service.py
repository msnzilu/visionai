
import logging
import asyncio
import random
from typing import Dict, Any, Optional

from app.database import get_users_collection, get_database
from app.core.security import (
    create_password_reset_token,
    verify_password_reset_token,
    hash_password,
    verify_password
)
from app.services.emails.email_service import EmailService

logger = logging.getLogger(__name__)

class PasswordService:
    """
    Service to handle password related operations:
    - Forgot Password (Request Reset)
    - Reset Password (Confirm Reset)
    - Change Password
    """

    @staticmethod
    async def request_password_reset(email: str) -> bool:
        """
        Initiate the password reset flow.
        1. Check if user exists.
        2. Generate generic reset token.
        3. Send email with link.
        """
        try:
            users_collection = await get_users_collection()
            user = await users_collection.find_one({"email": email})

            # Security: Always return True to prevent email enumeration
            if not user:
                logger.info(f"Password reset requested for non-existent email: {email}")
                # Fake processing time to mitigate timing attacks
                await asyncio.sleep(random.uniform(0.1, 0.5))
                return True

            # Generate Reset Token
            token = create_password_reset_token(email)

            # Send Email
            # We don't await this if we want it to be faster, but for now we await to ensure sending
            sent = await EmailService.send_password_reset_email(email, token)
            
            if not sent:
                logger.error(f"Failed to send password reset email to {email}")
                # We still return True to the user for security reasons? 
                # Or False to let them know something broke?
                # Usually better to say "If account exists..."
                return True 

            return True

        except Exception as e:
            logger.error(f"Error in request_password_reset: {str(e)}")
            # For system errors, we might want to return False or raise
            return False

    @staticmethod
    async def reset_password(token: str, new_password: str) -> Dict[str, Any]:
        """
        Complete the password reset.
        1. Verify Token.
        2. Update Password in DB.
        """
        try:
            # 1. Verify Token
            email = verify_password_reset_token(token)
            if not email:
                return {
                    "success": False,
                    "message": "Invalid or expired reset token"
                }

            users_collection = await get_users_collection()
            user = await users_collection.find_one({"email": email})
            
            if not user:
                return {
                    "success": False,
                    "message": "User not found"
                }

            # 2. Update Password
            new_password_hash = hash_password(new_password)
            
            # Update and also invalidate any existing sessions (optional, but good practice. 
            # Since we use stateless JWTs, we can't easily invalidate without a blacklist, 
            # but we can track 'password_changed_at' if we wanted).
            
            await users_collection.update_one(
                {"email": email},
                {"$set": {"password": new_password_hash}}
            )

            logger.info(f"Password reset successfully for user: {email}")
            
            return {
                "success": True,
                "message": "Password has been reset successfully. You can now login."
            }

        except Exception as e:
            logger.error(f"Error in reset_password: {str(e)}")
            return {
                "success": False,
                "message": "An error occurred while resetting password"
            }

    @staticmethod
    async def change_password(user_id: str, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change authenticated user's password.
        """
        try:
            users_collection = await get_users_collection()
            from bson import ObjectId
            
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return {"success": False, "message": "User not found"}
                
            if not verify_password(current_password, user["password"]):
                return {"success": False, "message": "Incorrect current password"}

            new_password_hash = hash_password(new_password)
            
            await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": new_password_hash}}
            )
            
            return {"success": True, "message": "Password updated successfully"}
            
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return {"success": False, "message": "Failed to update password"}
