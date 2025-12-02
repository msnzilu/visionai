# backend/app/api/email_applications.py
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from app.database import get_applications_collection, get_jobs_collection, get_users_collection, get_database
from app.models.application import Application, ApplicationStatus, ApplicationSource
from app.models.common import SuccessResponse
from app.models.user import User
from app.services.gmail_service import gmail_service
from app.api.auth import get_current_user
from app.models.email_log import EmailLog, EmailDirection, EmailStatus

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

class EmailApplicationRequest(BaseModel):
    job_id: str
    cv_id: Optional[str] = None # ID of the CV document to attach
    cover_letter: Optional[str] = None # Text content
    subject_template: Optional[str] = "Application for {job_title} - {full_name}"

class EmailApplicationResponse(BaseModel):
    success: bool
    message: str
    application_id: Optional[str] = None
    thread_id: Optional[str] = None

@router.post("/apply", response_model=EmailApplicationResponse)
async def apply_via_email(
    request: EmailApplicationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Apply for a job via email using the user's connected Gmail account.
    """
    try:
        # 1. Validate User has Gmail Connected
        if not current_user.get("gmail_auth"):
            raise HTTPException(
                status_code=400, 
                detail="Gmail account not connected. Please connect your Gmail account first."
            )
        
        # 2. Get Job Details
        jobs_collection = await get_jobs_collection()
        job = await jobs_collection.find_one({"_id": ObjectId(request.job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        employer_email = job.get("application_email") or job.get("contact_email")
        if not employer_email:
             raise HTTPException(status_code=400, detail="This job does not have an email address for applications.")

        # 3. Prepare Email Content
        user_full_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        job_title = job.get("title", "Job")
        
        subject = request.subject_template.format(
            job_title=job_title,
            full_name=user_full_name
        )
        
        body = request.cover_letter or f"Dear Hiring Manager,\n\nPlease find attached my application for the {job_title} position.\n\nSincerely,\n{user_full_name}"
        
        # TODO: Handle attachments (CV)
        # For now, we'll assume no attachments or implement fetching from documents collection later
        attachments = [] 
        
        # 4. Send Email via Gmail Service
        # We need to convert the dict back to GmailAuth model
        from app.models.user import GmailAuth
        gmail_auth = GmailAuth(**current_user["gmail_auth"])
        
        sent_message = gmail_service.send_email(
            auth=gmail_auth,
            to=employer_email,
            subject=subject,
            body=body,
            attachments=attachments
        )
        
        # 5. Create Application Record
        applications_collection = await get_applications_collection()
        
        application_doc = Application(
            job_id=request.job_id,
            user_id=str(current_user["_id"]),
            status=ApplicationStatus.SUBMITTED,
            source=ApplicationSource.DIRECT, # or EMAIL
            application_method="email",
            email_thread_id=sent_message.get("threadId"),
            last_email_at=datetime.utcnow(),
            email_status="sent",
            applied_date=datetime.utcnow(),
            job_title=job_title,
            company_name=job.get("company"),
            location=job.get("location")
        )
        
        result = await applications_collection.insert_one(application_doc.dict(by_alias=True, exclude={"id"}))
        application_id = str(result.inserted_id)
        
        # 6. Log Email
        # We can do this in background
        # background_tasks.add_task(log_email, ...)
        
        return EmailApplicationResponse(
            success=True,
            message="Application sent successfully",
            application_id=application_id,
            thread_id=sent_message.get("threadId")
        )

    except Exception as e:
        logger.error(f"Email application failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send application: {str(e)}")


class ManualTrackRequest(BaseModel):
    job_id: str
    application_url: Optional[str] = None
    notes: Optional[str] = None

@router.post("/track", response_model=EmailApplicationResponse)
async def track_external_application(
    request: ManualTrackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually track a job application submitted externally.
    """
    try:
        # 1. Get Job Details
        jobs_collection = await get_jobs_collection()
        job = await jobs_collection.find_one({"_id": ObjectId(request.job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # 2. Create Application Record
        applications_collection = await get_applications_collection()
        
        # Check if already applied
        existing = await applications_collection.find_one({
            "job_id": request.job_id,
            "user_id": str(current_user["_id"])
        })
        
        if existing:
             raise HTTPException(status_code=400, detail="You have already applied to this job.")

        application_doc = Application(
            job_id=request.job_id,
            user_id=str(current_user["_id"]),
            status=ApplicationStatus.SUBMITTED,
            source=ApplicationSource.MANUAL,
            application_method="external",
            application_url=request.application_url or job.get("application_url"),
            applied_date=datetime.utcnow(),
            job_title=job.get("title", "Job"),
            company_name=job.get("company"),
            location=job.get("location"),
            additional_notes=request.notes
        )
        
        result = await applications_collection.insert_one(application_doc.dict(by_alias=True, exclude={"id"}))
        
        return EmailApplicationResponse(
            success=True,
            message="Application tracked successfully",
            application_id=str(result.inserted_id)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual tracking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to track application: {str(e)}")

@router.get("/sync", response_model=SuccessResponse)
async def sync_inbox(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Trigger a background scan of the user's inbox for application updates.
    """
    try:
        from app.services.email_intelligence import EmailIntelligenceService
        service = EmailIntelligenceService(db)
        
        # Run in background to avoid timeout
        background_tasks.add_task(service.scan_inbox_for_replies, str(current_user["_id"]))
        
        return SuccessResponse(message="Inbox sync started in background")
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")
