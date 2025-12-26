# backend/app/services/automation/browser_automation_service.py
"""
Browser Automation Service - Integration with Node.js Playwright Microservice
Handles automated browser-based form filling and job application submission
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.core.config import settings

logger = logging.getLogger(__name__)

# Browser automation service URL (from docker-compose or config)
BROWSER_AUTOMATION_URL = getattr(settings, 'BROWSER_AUTOMATION_URL')


class BrowserAutomationService:
    """
    Service for automating job applications using Node.js browser automation microservice
    
    Architecture:
    - Python backend orchestrates the workflow
    - Node.js service handles actual Playwright browser automation
    - Communication via HTTP REST API
    """
    
    @staticmethod
    async def auto_apply_to_job(
        user_id: str,
        application_id: str,
        job_id: str,
        cv_id: Optional[str] = None
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
            cv_id: Optional specific CV ID to use
            
        Returns:
            Dict with automation result and status
        """
        try:
            logger.info(f"Starting browser auto-apply for user {user_id}, job {job_id}")
            
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
            
            # Get user's latest CV or specific CV
            logger.info(f"Looking up CV data for user {user_id}, specific cv_id: {cv_id}")
            cv_data = await BrowserAutomationService._get_user_cv_data(user_id, cv_id)
            if not cv_data:
                logger.error(f"Failed to find CV data for user {user_id} (cv_id: {cv_id})")
                raise ValueError("User has no CV uploaded or CV is not yet analyzed")
            
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
            automation_result = await BrowserAutomationService._call_browser_automation_service(
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
                logger.info(f"Browser auto-apply successful for application {application_id}")
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
                logger.error(f"Browser auto-apply failed for application {application_id}: {automation_result.get('error')}")
            
            return automation_result
            
        except Exception as e:
            logger.error(f"Error in browser auto_apply_to_job: {str(e)}")
            
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
    async def _get_user_cv_data(user_id: str, cv_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get user's CV data (optionally by specific ID)
        
        Args:
            user_id: User ID
            cv_id: Optional specific CV document ID
            
        Returns:
            Dict with CV data or None
        """
        try:
            db = await get_database()
            
            # Handle both string and ObjectId for user_id to be robust
            user_id_obj = None
            try:
                user_id_obj = ObjectId(user_id)
            except:
                pass
                
            user_ids = [user_id]
            if user_id_obj:
                user_ids.append(user_id_obj)

            query = {
                "user_id": {"$in": user_ids},
                "document_type": "cv",
                "cv_data": {"$exists": True, "$ne": None}
            }
            
            if cv_id:
                try:
                    query["_id"] = ObjectId(cv_id)
                except Exception as e:
                    logger.error(f"Invalid cv_id format: {cv_id}")
                    return None
            
            logger.info(f"CV Query: {query}")
                
            # Find document
            cv_doc = await db.documents.find_one(
                query,
                sort=[("upload_date", -1)]
            )
            
            if not cv_doc:
                logger.warning(f"No CV found with complete parsed data")
                if cv_id:
                    exists = await db.documents.find_one({"_id": ObjectId(cv_id)})
                    if exists:
                        logger.warning(f"Document {cv_id} exists but missing/null cv_data or wrong user/type")
                    else:
                        logger.error(f"Document {cv_id} NOT FOUND in database")
                return None
            
            logger.info(f"Successfully found CV data for document {cv_doc.get('_id')}")
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
                "session_id": application_id,
                "url": application_url,
                "autofill_data": {
                    "personal_info": user_data.get("personal_info", {}),
                    "experience": user_data.get("experience", []),
                    "education": user_data.get("education", []),
                    "skills": user_data.get("skills", {})
                },
                "job_source": BrowserAutomationService.detect_application_platform(application_url)
            }
            
            # Use authentication token from settings
            headers = {
                "Authorization": f"Bearer {settings.BROWSER_AUTOMATION_TOKEN}"
            }
            
            # Call Node.js automation service
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{BROWSER_AUTOMATION_URL}/api/automation/start",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Browser automation started: {result.get('status')}")
                    return {
                        "success": True, 
                        "session_id": result.get("browser_session_id"),
                        "status": result.get("status")
                    }
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
    async def check_application_status(
        application_id: str,
        user_id: str, 
        job_url: str
    ) -> Dict[str, Any]:
        """
        Hyper-Monitoring: Check application status via Browser + Email Domain Scan
        """
        try:
            db = await get_database()
            result_summary = {
                "portal_status": "unknown",
                "email_status": "unknown",
                "final_status": "unknown",
                "signals": []
            }

            # 1. BROWSER CHECK
            if job_url:
                try:
                    payload = {"url": job_url}
                    headers = {"Authorization": f"Bearer {settings.BROWSER_AUTOMATION_TOKEN}"}
                    
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            f"{BROWSER_AUTOMATION_URL}/api/automation/check-status",
                            json=payload,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            browser_data = response.json()
                            if browser_data.get("success"):
                                result_summary["portal_status"] = browser_data.get("status", "unknown")
                                result_summary["signals"].append({
                                    "source": "browser", 
                                    "status": result_summary["portal_status"],
                                    "detail": browser_data.get("matched_keyword"),
                                    "screenshot": browser_data.get("screenshot_base64")
                                })
                except Exception as browser_error:
                    logger.warning(f"Browser check failed: {browser_error}")

            # 2. EMAIL DOMAIN CHECK
            domain = ""
            try:
                from urllib.parse import urlparse
                domain = urlparse(job_url).netloc
                if domain.startswith("www."):
                    domain = domain[4:]
            except:
                pass

            if domain:
                try:
                    from app.services.emails.email_intelligence import EmailIntelligenceService
                    email_service = EmailIntelligenceService(db)
                    
                    email_updates = await email_service.scan_for_application_domain(
                        user_id=user_id,
                        domain=domain,
                        application_id=application_id
                    )
                    
                    if email_updates:
                        latest_update = email_updates[0]
                        result_summary["email_status"] = latest_update["analysis"].category.value
                        result_summary["signals"].append({
                            "source": "email_domain",
                            "status": result_summary["email_status"],
                            "detail": latest_update["subject"],
                            "timestamp": latest_update["timestamp"].isoformat()
                        })
                except Exception as email_error:
                    logger.warning(f"Email domain check failed: {email_error}")

            # 3. SYNTHESIS
            statuses = [s["status"] for s in result_summary["signals"]]
            
            if "rejected" in statuses:
                result_summary["final_status"] = "rejected"
            elif "offer" in statuses:
                result_summary["final_status"] = "offer"
            elif "interview" in statuses:
                result_summary["final_status"] = "interview"
            elif "in_review" in statuses:
                result_summary["final_status"] = "in_review"
            elif "applied" in statuses:
                result_summary["final_status"] = "applied"
            
            # Update Application if new info found
            if result_summary["final_status"] != "unknown":
                update_fields = {
                    "last_response_check": datetime.utcnow(),
                    "response_check_result": result_summary["final_status"]
                }
                
                status_mapping = {
                    "rejected": "rejected",
                    "offer": "offer_received", 
                    "interview": "interview_scheduled",
                    "in_review": "under_review",
                    "applied": "applied"
                }
                
                db_status = status_mapping.get(result_summary["final_status"])
                if db_status:
                    update_fields["status"] = db_status

                await db.applications.update_one(
                    {"_id": ObjectId(application_id)},
                    {"$set": update_fields}
                )

            return result_summary

        except Exception as e:
            logger.error(f"Error in hybrid status check: {e}")
            return {"error": str(e)}

    
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


# Configuration helper
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
