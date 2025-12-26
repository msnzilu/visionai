# backend/app/services/automation/quick_apply_service.py
"""
Quick Apply Service - Email-based job application automation
Handles applications via email when recruiter contact information is available
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.services.emails.email_agent_service import email_agent_service

logger = logging.getLogger(__name__)


class QuickApplyService:
    """
    Service for handling email-based "quick apply" applications
    
    Quick apply in this context means:
    - Application sent directly via email to recruiter/company
    - Does NOT require browser automation
    - Faster and more reliable than browser automation
    - Used when job posting includes recruiter email
    """
    
    @staticmethod
    async def quick_apply_via_email(
        user_id: str,
        application_id: str,
        job_id: str,
        cv_id: str,
        cover_letter_id: str,
        recipient_email: str,
        form_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send job application via email (quick apply method)
        
        Args:
            user_id: User ID
            application_id: Application record ID
            job_id: Job ID
            cv_id: CV document ID
            cover_letter_id: Cover letter document ID
            recipient_email: Recruiter/company email
            form_data: Optional pre-extracted form data
            
        Returns:
            Dict with result
        """
        try:
            logger.info(f"Quick apply via email for user {user_id}, job {job_id}")
            
            db = await get_database()
            
            # Get CV data if form_data not provided
            if not form_data:
                cv_doc = await db.documents.find_one({"_id": ObjectId(cv_id)})
                if cv_doc and cv_doc.get("cv_data"):
                    form_data = await email_agent_service.extract_form_data_from_cv(
                        user_id=user_id,
                        cv_data=cv_doc["cv_data"],
                        db=db
                    )
                else:
                    logger.error(f"CV document {cv_id} not found or has no cv_data")
                    return {
                        "success": False,
                        "error": "CV data not available",
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # Queue email sending via Celery worker
            from app.workers.email_sender import send_application_email
            send_application_email.delay(
                user_id=user_id,
                job_id=job_id,
                application_id=application_id,
                recipient_email=recipient_email,
                form_data=form_data,
                cv_document_id=cv_id,
                cover_letter_document_id=cover_letter_id,
                additional_message=None
            )
            
            logger.info(f"Successfully queued email application for job {job_id}")
            
            return {
                "success": True,
                "method": "email",
                "recipient": recipient_email,
                "message": "Application email queued successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in quick apply via email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    @staticmethod
    def has_recruiter_email(job: Dict[str, Any]) -> Optional[str]:
        """
        Check if job has recruiter/company email and return it
        
        Args:
            job: Job document
            
        Returns:
            Email address if found, None otherwise
        """
        # Priority order for email extraction
        email = (
            job.get("application_email") or 
            job.get("contact_email") or 
            job.get("email") or 
            (job.get("company_info", {}) or {}).get("contact", {}).get("email")
        )
        
        return email if email else None
    
    
    @staticmethod
    def supports_quick_apply(job: Dict[str, Any]) -> bool:
        """
        Check if a job supports quick apply (email-based)
        
        Args:
            job: Job document
            
        Returns:
            True if recruiter email is available
        """
        return QuickApplyService.has_recruiter_email(job) is not None
