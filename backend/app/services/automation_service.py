# backend/app/services/automation_service.py
"""
Browser Automation Service - Integration with Node.js Microservice
Handles automated form filling and job application submission
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.config import settings

logger = logging.getLogger(__name__)

# Browser automation service URL (from docker-compose or config)
BROWSER_AUTOMATION_URL = getattr(settings, 'BROWSER_AUTOMATION_URL')

class AutomationService:
    """
    Service for automating job applications using Node.js browser automation microservice
    
    Architecture:
    - Python backend orchestrates the workflow
    - Node.js service handles actual browser automation
    - Communication via HTTP REST API
    """
    
    @staticmethod
    async def auto_apply_to_job(
        user_id: str,
        application_id: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Automate job application submission via Node.js browser automation service
        
        Workflow:
        1. Loads user CV and profile data from database
        2. Gets job application URL
        3. Calls Node.js automation service with prepared data
        4. Node.js service opens browser, fills forms, submits
        5. Updates application status based on result
        
        Args:
            user_id: User ID performing the application
            application_id: Application record ID
            job_id: Job ID to apply for
            
        Returns:
            Dict with automation result and status
        """
        try:
            logger.info(f"Starting auto-apply for user {user_id}, job {job_id}")
            
            db = await get_database()
            
            # Step 1: Get job details
            job = await db.jobs.find_one({"_id": ObjectId(job_id)})
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            application_url = job.get("external_url") or job.get("apply_url")
            if not application_url:
                raise ValueError("Job has no application URL")
            
            # Step 2: Get user's CV and profile data
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get user's latest CV
            cv_data = await AutomationService._get_user_cv_data(user_id)
            if not cv_data:
                raise ValueError("User has no CV uploaded")
            
            # Step 3: Update application status to "processing"
            await db.applications.update_one(
                {"_id": ObjectId(application_id)},
                {
                    "$set": {
                        "status": "processing",
                        "automation_status": "in_progress",
                        "automation_started_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Step 4: Call Node.js browser automation service
            automation_result = await AutomationService._call_browser_automation_service(
                application_url=application_url,
                user_data={
                    "personal_info": cv_data.get("personal_info", {}),
                    "experience": cv_data.get("experience", []),
                    "education": cv_data.get("education", []),
                    "skills": cv_data.get("skills", {})
                },
                job_data={
                    "title": job.get("title"),
                    "company": job.get("company_name"),
                    "location": job.get("location")
                },
                application_id=application_id
            )
            
            # Step 5: Update application with result
            if automation_result.get("success"):
                await db.applications.update_one(
                    {"_id": ObjectId(application_id)},
                    {
                        "$set": {
                            "status": "applied",
                            "automation_status": "completed",
                            "automation_completed_at": datetime.utcnow(),
                            "applied_date": datetime.utcnow(),
                            "automation_details": automation_result,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Auto-apply successful for application {application_id}")
            else:
                await db.applications.update_one(
                    {"_id": ObjectId(application_id)},
                    {
                        "$set": {
                            "status": "pending",
                            "automation_status": "failed",
                            "automation_error": automation_result.get("error"),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.error(f"Auto-apply failed for application {application_id}: {automation_result.get('error')}")
            
            return automation_result
            
        except Exception as e:
            logger.error(f"Error in auto_apply_to_job: {str(e)}")
            
            # Update application with error
            try:
                db = await get_database()
                await db.applications.update_one(
                    {"_id": ObjectId(application_id)},
                    {
                        "$set": {
                            "status": "pending",
                            "automation_status": "failed",
                            "automation_error": str(e),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            except Exception as db_error:
                logger.error(f"Failed to update application after error: {db_error}")
            
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    @staticmethod
    async def _get_user_cv_data(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's latest CV data
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with CV data or None
        """
        try:
            db = await get_database()
            
            # Find latest CV document
            cv_doc = await db.documents.find_one(
                {
                    "user_id": ObjectId(user_id),
                    "document_type": "cv",
                    "cv_data": {"$exists": True, "$ne": None}
                },
                sort=[("upload_date", -1)]
            )
            
            if not cv_doc:
                logger.warning(f"No CV found for user {user_id}")
                return None
            
            return cv_doc.get("cv_data")
            
        except Exception as e:
            logger.error(f"Error getting CV data: {str(e)}")
            return None
    
    
    @staticmethod
    async def _call_browser_automation_service(
        application_url: str,
        user_data: Dict[str, Any],
        job_data: Dict[str, Any],
        application_id: str
    ) -> Dict[str, Any]:
        """
        Call Node.js browser automation service
        
        This sends a request to your existing browser-automation microservice
        which handles the actual Puppeteer/browser automation
        
        Args:
            application_url: URL of job application page
            user_data: User profile and CV information
            job_data: Job posting details
            application_id: Application ID for tracking
            
        Returns:
            Dict with automation result from Node.js service
        """
        try:
            logger.info(f"Calling browser automation service for URL: {application_url}")
            
            # Prepare request payload for Node.js service
            payload = {
                "url": application_url,
                "user_data": {
                    "personal_info": user_data.get("personal_info", {}),
                    "experience": user_data.get("experience", []),
                    "education": user_data.get("education", []),
                    "skills": user_data.get("skills", {})
                },
                "job_data": job_data,
                "application_id": application_id,
                "options": {
                    "headless": True,
                    "screenshot": True,
                    "timeout": 60000  # 60 seconds
                }
            }
            
            # Call Node.js automation service
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{BROWSER_AUTOMATION_URL}/api/autofill",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Browser automation completed: {result.get('success')}")
                    return result
                else:
                    error_msg = f"Browser automation service error: {response.status_code}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "status_code": response.status_code,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to browser automation service at {BROWSER_AUTOMATION_URL}"
            logger.error(f"{error_msg}: {str(e)}")
            return {
                "success": False,
                "error": error_msg,
                "note": "Ensure browser-automation service is running",
                "timestamp": datetime.utcnow().isoformat()
            }
        except httpx.TimeoutException:
            error_msg = "Browser automation timed out"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Browser automation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    @staticmethod
    async def get_automation_status(application_id: str) -> Dict[str, Any]:
        """
        Get current automation status for an application
        
        Args:
            application_id: Application ID
            
        Returns:
            Dict with automation status details
        """
        try:
            db = await get_database()
            
            application = await db.applications.find_one(
                {"_id": ObjectId(application_id)},
                {
                    "automation_status": 1,
                    "automation_started_at": 1,
                    "automation_completed_at": 1,
                    "automation_error": 1,
                    "automation_details": 1
                }
            )
            
            if not application:
                return {
                    "found": False,
                    "error": "Application not found"
                }
            
            return {
                "found": True,
                "status": application.get("automation_status", "not_started"),
                "started_at": application.get("automation_started_at"),
                "completed_at": application.get("automation_completed_at"),
                "error": application.get("automation_error"),
                "details": application.get("automation_details")
            }
            
        except Exception as e:
            logger.error(f"Error getting automation status: {str(e)}")
            return {
                "found": False,
                "error": str(e)
            }
    
    
    @staticmethod
    async def cancel_automation(application_id: str) -> bool:
        """
        Cancel ongoing automation for an application
        
        Args:
            application_id: Application ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            db = await get_database()
            
            # Update application status
            result = await db.applications.update_one(
                {
                    "_id": ObjectId(application_id),
                    "automation_status": "in_progress"
                },
                {
                    "$set": {
                        "automation_status": "cancelled",
                        "status": "pending",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Try to notify Node.js service to cancel
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        await client.post(
                            f"{BROWSER_AUTOMATION_URL}/api/cancel",
                            json={"application_id": application_id}
                        )
                except Exception as e:
                    logger.warning(f"Failed to notify browser service of cancellation: {e}")
                
                logger.info(f"Automation cancelled for application {application_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling automation: {str(e)}")
            return False
    
    
    @staticmethod
    def detect_application_platform(url: str) -> str:
        """
        Detect the job application platform from URL
        
        Args:
            url: Application URL
            
        Returns:
            Platform name (linkedin, indeed, greenhouse, lever, custom)
        """
        url_lower = url.lower()
        
        if "linkedin.com" in url_lower:
            return "linkedin"
        elif "indeed.com" in url_lower:
            return "indeed"
        elif "greenhouse.io" in url_lower:
            return "greenhouse"
        elif "lever.co" in url_lower:
            return "lever"
        elif "workday.com" in url_lower or "myworkdayjobs.com" in url_lower:
            return "workday"
        elif "icims.com" in url_lower:
            return "icims"
        else:
            return "custom"
    
    
    @staticmethod
    async def check_automation_service_health() -> Dict[str, Any]:
        """
        Check if browser automation service is running
        
        Returns:
            Dict with health status
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{BROWSER_AUTOMATION_URL}/health")
                
                if response.status_code == 200:
                    return {
                        "healthy": True,
                        "service": "browser-automation",
                        "url": BROWSER_AUTOMATION_URL,
                        "response": response.json()
                    }
                else:
                    return {
                        "healthy": False,
                        "service": "browser-automation",
                        "url": BROWSER_AUTOMATION_URL,
                        "status_code": response.status_code
                    }
        except Exception as e:
            return {
                "healthy": False,
                "service": "browser-automation",
                "url": BROWSER_AUTOMATION_URL,
                "error": str(e)
            }


# ============================================================================
# Configuration helper
# ============================================================================

def get_browser_automation_config() -> Dict[str, Any]:
    """
    Get browser automation service configuration
    
    Returns:
        Dict with configuration settings
    """
    return {
        "service_url": BROWSER_AUTOMATION_URL,
        "timeout": 120,
        "supported_platforms": [
            "linkedin",
            "indeed", 
            "greenhouse",
            "lever",
            "workday",
            "generic"
        ],
        "features": {
            "form_detection": True,
            "auto_fill": True,
            "document_upload": True,
            "screenshot": True,
            "multi_page": True
        }
    }