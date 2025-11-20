# backend/app/api/browser_automation.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import logging
from datetime import datetime

from app.database import get_database
from app.api.deps import get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class AutofillRequest(BaseModel):
    job_id: str
    cv_id: Optional[str] = None
    cover_letter_id: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None

class AutofillResponse(BaseModel):
    session_id: str
    status: str
    message: str
    browser_url: Optional[str] = None

@router.post("/autofill/start", response_model=AutofillResponse)
async def start_autofill_session(
    request: AutofillRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a browser automation session for job application.
    This endpoint communicates with the browser-automation service
    to open a browser instance with pre-filled data.
    """
    db = await get_database()
    
    # Get job details
    job = await db.jobs.find_one({"_id": request.job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.get("external_url") and not job.get("apply_url"):
        raise HTTPException(
            status_code=400,
            detail="This job doesn't have an application URL"
        )
    
    # Get CV data if provided
    cv_data = None
    if request.cv_id:
        cv_doc = await db.documents.find_one({
            "_id": request.cv_id,
            "user_id": current_user["id"]
        })
        if cv_doc:
            cv_data = cv_doc.get("parsed_data", {})
    
    # Get cover letter if provided
    cover_letter_content = None
    if request.cover_letter_id:
        cover_letter = await db.documents.find_one({
            "_id": request.cover_letter_id,
            "user_id": current_user["id"]
        })
        if cover_letter:
            cover_letter_content = cover_letter.get("content", "")
    
    # Prepare autofill data
    autofill_data = {
        "user": {
            "first_name": current_user.get("first_name", ""),
            "last_name": current_user.get("last_name", ""),
            "email": current_user.get("email", ""),
            "phone": current_user.get("phone", ""),
            "address": current_user.get("address", ""),
            "city": current_user.get("city", ""),
            "state": current_user.get("state", ""),
            "zip_code": current_user.get("zip_code", ""),
            "country": current_user.get("country", ""),
        },
        "cv_data": cv_data,
        "cover_letter": cover_letter_content,
        "job": {
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "url": job.get("external_url") or job.get("apply_url")
        }
    }
    
    # Add custom data if provided
    if request.custom_data:
        autofill_data.update(request.custom_data)
    
    # Create session record
    session_id = f"session_{current_user['id']}_{int(datetime.utcnow().timestamp())}"
    session_record = {
        "_id": session_id,
        "user_id": current_user["id"],
        "job_id": request.job_id,
        "status": "pending",
        "autofill_data": autofill_data,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.automation_sessions.insert_one(session_record)
    
    # Call browser automation service
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.AUTOMATION_SERVICE_URL}/api/automation/start",
                json={
                    "session_id": session_id,
                    "url": job.get("external_url") or job.get("apply_url"),
                    "autofill_data": autofill_data,
                    "job_source": job.get("source", "unknown")
                },
                headers={
                    "Authorization": f"Bearer {settings.AUTOMATION_SERVICE_TOKEN}"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update session status
                await db.automation_sessions.update_one(
                    {"_id": session_id},
                    {
                        "$set": {
                            "status": "started",
                            "browser_session": result.get("browser_session_id"),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                return AutofillResponse(
                    session_id=session_id,
                    status="started",
                    message="Browser automation started successfully",
                    browser_url=job.get("external_url") or job.get("apply_url")
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Browser automation service error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to automation service: {e}")
        raise HTTPException(
            status_code=503,
            detail="Browser automation service unavailable. Please try again later."
        )

@router.get("/autofill/status/{session_id}")
async def get_autofill_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a browser automation session"""
    db = await get_database()
    
    session = await db.automation_sessions.find_one({
        "_id": session_id,
        "user_id": current_user["id"]
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session.get("status", "unknown"),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
        "filled_fields": session.get("filled_fields", []),
        "errors": session.get("errors", [])
    }

@router.post("/autofill/feedback/{session_id}")
async def submit_feedback(
    session_id: str,
    corrections: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Submit feedback for ML model training.
    Records user corrections to improve autofill accuracy.
    """
    db = await get_database()
    
    session = await db.automation_sessions.find_one({
        "_id": session_id,
        "user_id": current_user["id"]
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store feedback for ML training
    feedback_record = {
        "session_id": session_id,
        "user_id": current_user["id"],
        "job_id": session.get("job_id"),
        "corrections": corrections,
        "original_data": session.get("autofill_data"),
        "created_at": datetime.utcnow()
    }
    
    await db.autofill_feedback.insert_one(feedback_record)
    
    # Update session with feedback
    await db.automation_sessions.update_one(
        {"_id": session_id},
        {
            "$set": {
                "has_feedback": True,
                "feedback_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Feedback recorded successfully"}