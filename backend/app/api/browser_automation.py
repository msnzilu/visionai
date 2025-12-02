# backend/app/api/browser_automation.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import logging
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.api.deps import get_current_user
from app.core.config import settings

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


def get_user_id(user: dict) -> str:
    """Extract user ID from user dict, handling both 'id' and '_id' keys"""
    return str(user.get("id") or user.get("_id") or user.get("user_id", ""))


def safe_object_id(id_str: str):
    """Safely convert string to ObjectId, return original if invalid"""
    try:
        return ObjectId(id_str)
    except:
        return id_str


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
    try:
        db = await get_database()
        user_id = get_user_id(current_user)
        
        if not user_id:
            logger.error(f"Invalid user object: {current_user}")
            raise HTTPException(
                status_code=401,
                detail="Invalid user session. Please login again."
            )
        
        logger.info(f"Starting autofill for user {user_id}, job {request.job_id}")
        
        # Get job details - try both ID formats
        job = None
        job_id_obj = safe_object_id(request.job_id)
        
        job = await db.jobs.find_one({"_id": job_id_obj})
        if not job:
            # Try with string ID
            job = await db.jobs.find_one({"_id": request.job_id})
        
        if not job:
            logger.error(f"Job not found with ID: {request.job_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Job not found with ID: {request.job_id}"
            )
        
        if not job.get("external_url") and not job.get("apply_url"):
            raise HTTPException(
                status_code=400,
                detail="This job doesn't have an application URL"
            )
        
        # Get CV data if provided
        cv_data = None
        if request.cv_id:
            cv_id_obj = safe_object_id(request.cv_id)
            user_id_obj = safe_object_id(user_id)
            
            cv_doc = await db.documents.find_one({
                "_id": cv_id_obj,
                "user_id": user_id_obj
            })
            
            if not cv_doc:
                # Try with string IDs
                cv_doc = await db.documents.find_one({
                    "_id": request.cv_id,
                    "user_id": user_id
                })
            
            if cv_doc:
                cv_data = cv_doc.get("parsed_data", {})
                logger.info(f"Found CV document for user {user_id}")
            else:
                logger.warning(f"CV not found: {request.cv_id} for user {user_id}")
        
        # Get cover letter if provided
        cover_letter_content = None
        if request.cover_letter_id:
            cl_id_obj = safe_object_id(request.cover_letter_id)
            user_id_obj = safe_object_id(user_id)
            
            cover_letter = await db.documents.find_one({
                "_id": cl_id_obj,
                "user_id": user_id_obj
            })
            
            if not cover_letter:
                cover_letter = await db.documents.find_one({
                    "_id": request.cover_letter_id,
                    "user_id": user_id
                })
            
            if cover_letter:
                cover_letter_content = cover_letter.get("content", "")
                logger.info(f"Found cover letter for user {user_id}")
        
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
        session_id = f"session_{user_id}_{int(datetime.utcnow().timestamp())}"
        session_record = {
            "_id": session_id,
            "user_id": user_id,
            "job_id": request.job_id,
            "status": "pending",
            "autofill_data": autofill_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.automation_sessions.insert_one(session_record)
        logger.info(f"Created session: {session_id}")
        
        # Get automation service URL
        automation_url = getattr(settings, 'BROWSER_AUTOMATION_URL', None) or \
                       getattr(settings, 'AUTOMATION_SERVICE_URL', None) or \
                       "http://automation:3000"
        
        logger.info(f"Calling automation service at: {automation_url}")
        
        # Call browser automation service
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                automation_payload = {
                    "session_id": session_id,
                    "url": job.get("external_url") or job.get("apply_url"),
                    "autofill_data": autofill_data,
                    "job_source": job.get("source", "unknown")
                }
                
                logger.debug(f"Automation payload: {automation_payload}")
                
                response = await client.post(
                    f"{automation_url}/api/automation/start",
                    json=automation_payload,
                    headers={
                        "Authorization": f"Bearer {getattr(settings, 'AUTOMATION_SERVICE_TOKEN', '')}"
                    }
                )
                
                logger.info(f"Automation service response: {response.status_code}")
                
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
                    
                    logger.info(f"Session {session_id} started successfully")
                    
                    return AutofillResponse(
                        session_id=session_id,
                        status="started",
                        message="Browser automation started successfully",
                        browser_url=job.get("external_url") or job.get("apply_url")
                    )
                else:
                    error_text = response.text
                    logger.error(f"Automation service error: {response.status_code} - {error_text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Browser automation service error: {error_text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to automation service: {e}")
            raise HTTPException(
                status_code=503,
                detail="Browser automation service unavailable. Please try again later."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in start_autofill_session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/autofill/status/{session_id}")
async def get_autofill_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a browser automation session"""
    try:
        db = await get_database()
        user_id = get_user_id(current_user)
        
        session = await db.automation_sessions.find_one({
            "_id": session_id,
            "user_id": user_id
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    try:
        db = await get_database()
        user_id = get_user_id(current_user)
        
        session = await db.automation_sessions.find_one({
            "_id": session_id,
            "user_id": user_id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Store feedback for ML training
        feedback_record = {
            "session_id": session_id,
            "user_id": user_id,
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))