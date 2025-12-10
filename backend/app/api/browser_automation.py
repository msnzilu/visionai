# backend/app/api/browser_automation.py
"""
Quick Apply / Email Agent API
Handles intelligent form prefilling and email-based application submission
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.api.deps import get_current_user
from app.services.email_agent_service import email_agent_service
from app.schemas.quick_apply import (
    QuickApplyPrefillResponse,
    QuickApplySubmission,
    QuickApplySubmissionResponse,
    QuickApplyStatusResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_user_id(user: dict) -> str:
    """Extract user ID from user dict"""
    return str(user.get("id") or user.get("_id") or user.get("user_id", ""))


@router.post("/quick-apply/prefill", response_model=QuickApplyPrefillResponse)
async def prefill_quick_apply_form(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Prefill quick apply form with user's CV data
    
    This endpoint extracts data from the user's CV and returns
    form-ready data for the quick apply form.
    """
    try:
        user_id = get_user_id(current_user)
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid user session"
            )
        
        logger.info(f"Prefilling form for user {user_id}, job {job_id}")
        
        db = await get_database()
        
        # Get job details
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}"
            )
        
        # Extract form data from CV
        logger.info(f"Extracting form data from CV for user {user_id}")
        form_data = await email_agent_service.extract_form_data_from_cv(user_id)
        
        # Check for generated cover letter
        saved_job = await db.saved_jobs.find_one({
             "user_id": user_id,
             "job_id": job_id
        })
        
        if saved_job and saved_job.get("generated_cover_letter_id"):
             gen_cl_id = saved_job.get("generated_cover_letter_id")
             try:
                 gen_cl = await db.generated_documents.find_one({"_id": ObjectId(gen_cl_id)})
                 if gen_cl and "content" in gen_cl:
                      # Structure is content -> content -> full_text based on service
                      full_text = gen_cl.get("content", {}).get("content", {}).get("full_text")
                      if full_text:
                           form_data["cover_letter"] = full_text
                           logger.info(f"Injected generated cover letter text for user {user_id}")
             except Exception as e:
                 logger.warning(f"Failed to load generated cover letter content: {e}")

        logger.info(f"Extracted form data keys: {list(form_data.keys())}")
        logger.debug(f"Form data values: {form_data}")
        
        # Determine recipient email (prioritize application_email as per model)
        recipient_email = (
            job.get("application_email") or 
            job.get("contact_email") or 
            job.get("recruiter_email")
        )
        
        response_data = QuickApplyPrefillResponse(
            success=True,
            form_data=form_data,
            job_title=job.get("title", ""),
            company_name=job.get("company_name", ""),
            recipient_email=recipient_email,
            message="Form data loaded successfully"
        )
        
        logger.info(f"Returning prefill response with {len(form_data)} fields, recipient: {recipient_email}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error prefilling form: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prefill form: {str(e)}"
        )


@router.post("/quick-apply/submit", response_model=QuickApplySubmissionResponse)
async def submit_quick_apply(
    submission: QuickApplySubmission,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit job application via email agent
    
    This endpoint:
    1. Creates an application record
    2. Composes a professional application email
    3. Sends via user's Gmail account
    4. Tracks the application
    """
    try:
        user_id = get_user_id(current_user)
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid user session"
            )
        
        logger.info(f"Submitting application for user {user_id}, job {submission.job_id}")
        
        db = await get_database()
        
        # Check if user has Gmail connected
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("gmail_auth"):
            raise HTTPException(
                status_code=400,
                detail="Gmail not connected. Please connect your Gmail account to send applications."
            )
        
        # Get job details
        job = await db.jobs.find_one({"_id": ObjectId(submission.job_id)})
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {submission.job_id}"
            )
        
        # Check if application already exists
        existing_app = await db.applications.find_one({
            "user_id": user_id,
            "job_id": submission.job_id
        })
        
        if existing_app:
            raise HTTPException(
                status_code=409,
                detail="You have already applied to this job"
            )
        
        # Create application record
        application_doc = {
            "user_id": user_id,
            "job_id": submission.job_id,
            "status": "applied",
            "source": "auto_apply",
            "job_title": job.get("title"),
            "company_name": job.get("company_name"),
            "location": job.get("location"),
            "form_data": submission.form_data.dict(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None
        }
        
        try:
            result = await db.applications.insert_one(application_doc)
            application_id = str(result.inserted_id)
            
            logger.info(f"Created application record: {application_id}")
            
            # Send application via Gmail in background
            send_result = await email_agent_service.send_application_via_gmail(
                user_id=user_id,
                job_id=submission.job_id,
                application_id=application_id,
                recipient_email=submission.recipient_email,
                form_data=submission.form_data.dict(),
                cv_document_id=submission.cv_document_id,
                cover_letter_document_id=submission.cover_letter_document_id,
                additional_message=submission.additional_message
            )
            
            if send_result.get("success"):
                return QuickApplySubmissionResponse(
                    success=True,
                    application_id=application_id,
                    gmail_message_id=send_result.get("gmail_message_id"),
                    sent_at=datetime.fromisoformat(send_result.get("sent_at")),
                    recipient=send_result.get("recipient"),
                    message="Application sent successfully via email"
                )
            else:
                return QuickApplySubmissionResponse(
                    success=False,
                    application_id=application_id,
                    error=send_result.get("error"),
                    message="Failed to send application email"
                )

        except Exception as db_error:
            if "duplicate key error" in str(db_error):
                raise HTTPException(
                    status_code=409,
                    detail="You have already applied to this job"
                )
            raise db_error
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit application: {str(e)}"
        )


@router.get("/quick-apply/status/{application_id}", response_model=QuickApplyStatusResponse)
async def get_application_status(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get application submission and tracking status
    """
    try:
        user_id = get_user_id(current_user)
        
        db = await get_database()
        
        # Get application
        application = await db.applications.find_one({
            "_id": ObjectId(application_id),
            "user_id": user_id
        })
        
        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )
        
        return QuickApplyStatusResponse(
            application_id=application_id,
            status=application.get("status", "unknown"),
            email_sent_via=application.get("email_sent_via"),
            gmail_message_id=application.get("gmail_message_id"),
            email_sent_at=application.get("email_sent_at"),
            recipient_email=application.get("recipient_email"),
            response_received=application.get("response_received", False),
            response_at=application.get("response_at"),
            error_message=application.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Legacy endpoint compatibility (redirects to prefill)
@router.post("/autofill/start")
async def legacy_autofill_start(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Legacy endpoint - redirects to quick apply prefill
    """
    logger.warning("Legacy /autofill/start endpoint called, redirecting to /quick-apply/prefill")
    return await prefill_quick_apply_form(job_id, current_user)
