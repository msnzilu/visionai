# backend/app/services/email_agent_service.py
"""
Email Agent Service - AI-Powered Application Submission
Handles form prefilling, email composition, and application tracking via Gmail
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.services.gmail_service import gmail_service
from app.models.user import GmailAuth
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailAgentService:
    """
    Email Agent for intelligent job application submission
    
    Features:
    - Extract form data from CV
    - Compose professional application emails
    - Send via Gmail API
    - Track applications and responses
    """
    
    @staticmethod
    async def extract_form_data_from_cv(user_id: str, cv_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract form-fillable data from user's CV
        
        Args:
            user_id: User ID
            cv_data: Optional CV data (if not provided, fetches latest)
            
        Returns:
            Dict with form fields ready for prefilling
        """
        try:
            db = await get_database()
            
            # Get user data
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get CV data if not provided
            if not cv_data:
                cv_doc = await db.documents.find_one(
                    {
                        "user_id": ObjectId(user_id),
                        "document_type": "cv",
                        "is_active": True
                    },
                    sort=[("created_at", -1)]
                )
                
                if cv_doc:
                    cv_data = cv_doc.get("parsed_data", {})
            
            # Extract personal info from CV or user profile
            personal_info = cv_data.get("personal_info", {}) if cv_data else {}
            profile = user.get("profile", {}) or {}
            profile_personal = profile.get("personal_info", {}) if profile else {}
            
            # Build form data with fallbacks
            form_data = {
                "first_name": (
                    personal_info.get("first_name") or 
                    profile_personal.get("first_name") or 
                    user.get("first_name", "")
                ),
                "last_name": (
                    personal_info.get("last_name") or 
                    profile_personal.get("last_name") or 
                    user.get("last_name", "")
                ),
                "email": user.get("email", ""),
                "phone": (
                    personal_info.get("phone") or 
                    profile_personal.get("phone") or 
                    user.get("phone", "")
                ),
                "address": (
                    personal_info.get("address") or 
                    profile_personal.get("address", "")
                ),
                "city": (
                    personal_info.get("city") or 
                    profile_personal.get("city", "")
                ),
                "state": (
                    personal_info.get("state") or 
                    profile_personal.get("state", "")
                ),
                "country": (
                    personal_info.get("country") or 
                    profile_personal.get("country", "")
                ),
                "postal_code": (
                    personal_info.get("postal_code") or 
                    profile_personal.get("postal_code", "")
                ),
                "linkedin_url": (
                    personal_info.get("linkedin_url") or 
                    profile_personal.get("linkedin_url", "")
                ),
                "portfolio_url": (
                    personal_info.get("portfolio_url") or 
                    profile_personal.get("portfolio_url", "")
                ),
                "github_url": (
                    personal_info.get("github_url") or 
                    profile_personal.get("github_url", "")
                ),
            }
            
            # Add experience summary if available
            if cv_data and isinstance(cv_data, dict) and cv_data.get("experience"):
                experiences = cv_data.get("experience", [])
                if experiences and isinstance(experiences, list):
                    # Get years of experience
                    total_years = sum(exp.get("years", 0) for exp in experiences if isinstance(exp, dict))
                    form_data["years_of_experience"] = total_years
                    
                    # Get current/most recent position
                    if experiences:
                        latest_exp = experiences[0]
                        if isinstance(latest_exp, dict):
                            form_data["current_position"] = latest_exp.get("title", "")
                            form_data["current_company"] = latest_exp.get("company", "")
            
            # Add education if available
            if cv_data and isinstance(cv_data, dict) and cv_data.get("education"):
                education = cv_data.get("education", [])
                if education and isinstance(education, list):
                    latest_edu = education[0]
                    if isinstance(latest_edu, dict):
                        form_data["education_level"] = latest_edu.get("degree", "")
                        form_data["university"] = latest_edu.get("institution", "")
            
            # Add skills
            if cv_data and isinstance(cv_data, dict) and cv_data.get("skills"):
                skills = cv_data.get("skills", {})
                if isinstance(skills, dict):
                    form_data["skills"] = skills.get("technical", []) + skills.get("soft", [])
            elif profile and isinstance(profile, dict) and profile.get("skills"):
                form_data["skills"] = profile.get("skills", [])
            
            logger.info(f"Extracted form data for user {user_id}")
            return form_data
            
        except Exception as e:
            logger.error(f"Error extracting form data: {str(e)}")
            raise
    
    
    @staticmethod
    async def compose_application_email(
        job: Dict[str, Any],
        user: Dict[str, Any],
        form_data: Dict[str, Any],
        cover_letter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compose professional application email
        
        Args:
            job: Job posting data
            user: User data
            form_data: Form data from quick apply
            cover_letter: Optional cover letter content
            
        Returns:
            Dict with email subject, body, and metadata
        """
        try:
            # Extract job details
            job_title = job.get("title", "Position")
            company_name = job.get("company_name", "your company")
            
            # Build email subject
            subject = f"Application for {job_title} at {company_name}"
            
            # Build email body
            full_name = f"{form_data.get('first_name', '')} {form_data.get('last_name', '')}".strip()
            
            # Professional email template
            body_parts = []
            
            # Greeting
            body_parts.append(f"Dear Hiring Manager,\n")
            
            # Opening paragraph
            body_parts.append(
                f"I am writing to express my strong interest in the {job_title} position at {company_name}. "
                f"I believe my skills and experience make me an excellent candidate for this role.\n"
            )
            
            # Cover letter or experience summary
            if cover_letter:
                body_parts.append(f"\n{cover_letter}\n")
            else:
                # Auto-generate brief summary
                if form_data.get("years_of_experience"):
                    body_parts.append(
                        f"\nWith {form_data.get('years_of_experience')} years of professional experience"
                    )
                    if form_data.get("current_position"):
                        body_parts.append(f" as a {form_data.get('current_position')}")
                    body_parts.append(", I am confident in my ability to contribute to your team.\n")
            
            # Contact information
            body_parts.append("\nContact Information:")
            body_parts.append(f"Email: {form_data.get('email', '')}")
            if form_data.get("phone"):
                body_parts.append(f"Phone: {form_data.get('phone')}")
            if form_data.get("linkedin_url"):
                body_parts.append(f"LinkedIn: {form_data.get('linkedin_url')}")
            if form_data.get("portfolio_url"):
                body_parts.append(f"Portfolio: {form_data.get('portfolio_url')}")
            
            # Closing
            body_parts.append(
                f"\n\nI have attached my resume for your review. "
                f"I would welcome the opportunity to discuss how my background and skills "
                f"would be a great fit for {company_name}.\n"
            )
            body_parts.append(f"\nThank you for your consideration.\n")
            body_parts.append(f"\nBest regards,\n{full_name}")
            
            body = "\n".join(body_parts)
            
            return {
                "subject": subject,
                "body": body,
                "from_name": full_name,
                "from_email": form_data.get("email", "")
            }
            
        except Exception as e:
            logger.error(f"Error composing email: {str(e)}")
            raise
    
    
    @staticmethod
    async def send_application_via_gmail(
        user_id: str,
        job_id: str,
        application_id: str,
        recipient_email: str,
        form_data: Dict[str, Any],
        cv_document_id: str,
        cover_letter_document_id: Optional[str] = None,
        additional_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send job application via Gmail API
        
        Args:
            user_id: User ID
            job_id: Job ID
            application_id: Application record ID
            recipient_email: Company/recruiter email
            form_data: Form data
            cv_document_id: CV document ID
            cover_letter_document_id: Optional cover letter document ID
            additional_message: Optional additional message
            
        Returns:
            Dict with send result and Gmail message ID
        """
        try:
            db = await get_database()
            
            # Get user and Gmail auth
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            gmail_auth_data = user.get("gmail_auth")
            if not gmail_auth_data:
                raise ValueError("Gmail not connected. Please connect your Gmail account first.")
            
            # Convert to GmailAuth model
            gmail_auth = GmailAuth(**gmail_auth_data)
            
            # Get job details
            job = await db.jobs.find_one({"_id": ObjectId(job_id)})
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Compose email
            email_data = await EmailAgentService.compose_application_email(
                job=job,
                user=user,
                form_data=form_data,
                cover_letter=additional_message
            )
            
            # Get CV document path
            attachments = []
            cv_doc = await db.documents.find_one({"_id": ObjectId(cv_document_id)})
            if cv_doc and cv_doc.get("file_path"):
                attachments.append(cv_doc.get("file_path"))
            
            # Get cover letter document if provided
            if cover_letter_document_id:
                cl_doc = await db.documents.find_one({"_id": ObjectId(cover_letter_document_id)})
                if cl_doc and cl_doc.get("file_path"):
                    attachments.append(cl_doc.get("file_path"))
            
            # Send email via Gmail
            logger.info(f"Sending application email to {recipient_email}")
            gmail_result = gmail_service.send_email(
                auth=gmail_auth,
                to=recipient_email,
                subject=email_data["subject"],
                body=email_data["body"],
                attachments=attachments
            )
            
            # Update application record
            await db.applications.update_one(
                {"_id": ObjectId(application_id)},
                {
                    "$set": {
                        "status": "applied",
                        "applied_date": datetime.utcnow(),
                        "email_sent_via": "gmail",
                        "gmail_message_id": gmail_result.get("id"),
                        "email_sent_at": datetime.utcnow(),
                        "recipient_email": recipient_email,
                        "email_subject": email_data["subject"],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Track email in email_logs
            await db.email_logs.insert_one({
                "user_id": ObjectId(user_id),
                "application_id": ObjectId(application_id),
                "job_id": ObjectId(job_id),
                "gmail_message_id": gmail_result.get("id"),
                "recipient": recipient_email,
                "subject": email_data["subject"],
                "sent_at": datetime.utcnow(),
                "status": "sent"
            })
            
            logger.info(f"Application sent successfully via Gmail: {gmail_result.get('id')}")
            
            return {
                "success": True,
                "gmail_message_id": gmail_result.get("id"),
                "sent_at": datetime.utcnow().isoformat(),
                "recipient": recipient_email
            }
            
        except Exception as e:
            logger.error(f"Error sending application via Gmail: {str(e)}")
            
            # Update application with error
            try:
                db = await get_database()
                await db.applications.update_one(
                    {"_id": ObjectId(application_id)},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": str(e),
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
    async def monitor_application_responses(user_id: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Monitor Gmail for application responses
        
        Args:
            user_id: User ID
            days_back: Number of days to look back
            
        Returns:
            List of detected responses
        """
        try:
            db = await get_database()
            
            # Get user and Gmail auth
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("gmail_auth"):
                return []
            
            gmail_auth = GmailAuth(**user.get("gmail_auth"))
            
            # Get recent applications
            applications = await db.applications.find({
                "user_id": ObjectId(user_id),
                "email_sent_via": "gmail",
                "gmail_message_id": {"$exists": True}
            }).to_list(length=100)
            
            responses = []
            
            # Check for responses to each application
            for app in applications:
                gmail_message_id = app.get("gmail_message_id")
                recipient_email = app.get("recipient_email")
                
                if not recipient_email:
                    continue
                
                # Search for emails from the recipient
                query = f"from:{recipient_email}"
                messages = gmail_service.list_messages(
                    auth=gmail_auth,
                    query=query,
                    max_results=10
                )
                
                if messages:
                    # Update application status
                    await db.applications.update_one(
                        {"_id": app["_id"]},
                        {
                            "$set": {
                                "response_received": True,
                                "response_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    responses.append({
                        "application_id": str(app["_id"]),
                        "job_id": str(app.get("job_id")),
                        "response_count": len(messages),
                        "detected_at": datetime.utcnow().isoformat()
                    })
            
            logger.info(f"Monitored {len(applications)} applications, found {len(responses)} responses")
            return responses
            
        except Exception as e:
            logger.error(f"Error monitoring responses: {str(e)}")
            return []


# Singleton instance
email_agent_service = EmailAgentService()
