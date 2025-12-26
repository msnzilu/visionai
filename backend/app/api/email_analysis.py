# backend/app/api/email_analysis.py
"""
Email Analysis API Endpoints
Provides endpoints for analyzing emails and processing email responses
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.models.email_analysis import (
    EmailAnalysisResult,
    ApplicationUpdateResult,
    AnalyzeEmailRequest,
    EmailResponseData
)
from app.models.user import User
from app.api.deps import get_current_user
from app.services.emails.email_response_analyzer import email_response_analyzer
from app.services.emails.gmail_service import gmail_service
from app.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze-email", response_model=EmailAnalysisResult)
async def analyze_email(
    request: AnalyzeEmailRequest,
    current_user: User = Depends(get_current_user)
) -> EmailAnalysisResult:
    """
    Analyze an email to determine its category and required actions
    
    This endpoint allows manual analysis of emails for testing or review purposes.
    """
    try:
        logger.info(f"Analyzing email for user {current_user.id}")
        
        result = await email_response_analyzer.analyze_email_response(
            email_content=request.email_content,
            email_subject=request.email_subject,
            sender_email=request.sender_email,
            application_id=request.application_id,
            use_ai=request.use_ai
        )
        
        logger.info(
            f"Email analysis complete: category={result.category}, "
            f"confidence={result.confidence:.2f}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze email: {str(e)}"
        )


@router.post("/applications/{application_id}/analyze-latest-email", response_model=EmailAnalysisResult)
async def analyze_latest_email_for_application(
    application_id: str,
    current_user: User = Depends(get_current_user)
) -> EmailAnalysisResult:
    """
    Analyze the latest email in an application's email thread
    
    Retrieves the latest email from the application's Gmail thread and analyzes it.
    """
    try:
        db = await get_database()
        applications_collection = db["applications"]
        
        # Get application
        app = await applications_collection.find_one({
            "_id": ObjectId(application_id),
            "user_id": str(current_user.id)
        })
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check if application has email thread
        if not app.get("email_thread_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application does not have an email thread"
            )
        
        # Get user's Gmail auth
        users_collection = db["users"]
        user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
        
        if not user or not user.get("gmail_auth"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail not connected for this user"
            )
        
        from app.models.user import GmailAuth
        gmail_auth = GmailAuth(**user["gmail_auth"])
        
        # Get latest message from thread
        thread_id = app["email_thread_id"]
        messages = gmail_service.list_messages(
            gmail_auth,
            query=f"threadId:{thread_id}",
            max_results=1
        )
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No messages found in email thread"
            )
        
        # Get message details
        message_detail = gmail_service.get_message(gmail_auth, messages[0]["id"])
        headers = {h["name"]: h["value"] for h in message_detail["payload"]["headers"]}
        
        sender = headers.get("From", "")
        subject = headers.get("Subject", "")
        snippet = message_detail.get("snippet", "")
        
        # Analyze email
        result = await email_response_analyzer.analyze_email_response(
            email_content=snippet,
            email_subject=subject,
            sender_email=sender,
            application_id=application_id,
            use_ai=True
        )
        
        logger.info(
            f"Analyzed latest email for application {application_id}: "
            f"category={result.category}, confidence={result.confidence:.2f}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing latest email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze latest email: {str(e)}"
        )


@router.post("/applications/{application_id}/process-email-response", response_model=ApplicationUpdateResult)
async def process_email_response(
    application_id: str,
    email_data: EmailResponseData,
    current_user: User = Depends(get_current_user)
) -> ApplicationUpdateResult:
    """
    Analyze an email response and update the application accordingly
    
    This endpoint analyzes the provided email and automatically updates
    the application status, creates tasks, or sets reminders based on the analysis.
    """
    try:
        db = await get_database()
        applications_collection = db["applications"]
        
        # Verify application exists and belongs to user
        app = await applications_collection.find_one({
            "_id": ObjectId(application_id),
            "user_id": str(current_user.id)
        })
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Analyze email
        logger.info(f"Processing email response for application {application_id}")
        
        analysis = await email_response_analyzer.analyze_email_response(
            email_content=email_data.email_content,
            email_subject=email_data.email_subject,
            sender_email=email_data.sender_email,
            application_id=application_id,
            use_ai=True
        )
        
        logger.info(
            f"Email analysis: category={analysis.category}, "
            f"confidence={analysis.confidence:.2f}, "
            f"requires_action={analysis.requires_action}"
        )
        
        # Update application based on analysis
        if analysis.requires_action and analysis.confidence >= email_response_analyzer.MIN_CONFIDENCE_FOR_STATUS_UPDATE:
            update_result = await email_response_analyzer.update_application_from_analysis(
                application_id=application_id,
                analysis_result=analysis,
                user_id=str(current_user.id)
            )
            
            logger.info(
                f"Application updated: success={update_result.success}, "
                f"actions={', '.join(update_result.actions_taken)}"
            )
            
            return update_result
        else:
            # Low confidence or no action required
            logger.info(
                f"No action taken: confidence={analysis.confidence:.2f}, "
                f"requires_action={analysis.requires_action}"
            )
            
            return ApplicationUpdateResult(
                success=True,
                application_id=application_id,
                actions_taken=["Email analyzed but no action required (low confidence or no action needed)"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing email response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process email response: {str(e)}"
        )
