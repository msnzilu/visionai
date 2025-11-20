# backend/app/api/applications.py
"""
Job application management API routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from bson import ObjectId

from app.api.deps import (
    CurrentActiveUser, CurrentVerifiedUser, CurrentAdminUser,
    ApplicationQueryParams, track_api_usage, check_feature_access,
    get_valid_object_id, check_user_ownership, check_cv_generation_limits,
    check_cover_letter_limits, check_auto_apply_limits
)
from app.models.application import (
    Application, ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    ApplicationListResponse, ApplicationStats, ApplicationStatus,
    CustomCV, CoverLetter, Interview, ApplicationTask
)
from app.models.common import SuccessResponse
from backend.app.services.application_tracking_service import ApplicationService
from app.services.ai_service import AIService
from app.services.automation_service import AutomationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_create: ApplicationCreate,
    current_user: Dict[str, Any] = CurrentVerifiedUser
):
    """
    Create a new job application
    """
    try:
        await track_api_usage("create_application", current_user)
        
        # Set user ID
        application_create.user_id = str(current_user["_id"])
        
        # Create application
        application_id = await ApplicationService.create_application(application_create)
        
        if not application_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create application"
            )
        
        # Get created application
        application = await ApplicationService.get_application_by_id(application_id)
        
        return ApplicationResponse(
            id=str(application["_id"]),
            job_id=str(application["job_id"]),
            user_id=str(application["user_id"]),
            status=application["status"],
            source=application["source"],
            applied_date=application.get("applied_date"),
            job_title=application.get("job_title"),
            company_name=application.get("company_name"),
            location=application.get("location"),
            priority=application["priority"],
            documents_count=len(application.get("documents", [])),
            communications_count=len(application.get("communications", [])),
            interviews_count=len(application.get("interviews", [])),
            tasks_count=len(application.get("tasks", [])),
            has_custom_cv=application.get("custom_cv") is not None,
            has_cover_letter=application.get("cover_letter") is not None,
            last_activity=application["updated_at"],
            created_at=application["created_at"],
            updated_at=application["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    query_params: ApplicationQueryParams = Depends(),
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    List user's applications with filtering and pagination
    """
    try:
        await track_api_usage("list_applications", current_user)
        
        # Build filter from query params
        filters = {}
        if query_params.status:
            filters["status"] = query_params.status
        if query_params.company:
            filters["company_name"] = {"$regex": query_params.company, "$options": "i"}
        if query_params.priority:
            filters["priority"] = query_params.priority
        
        # Date filters
        if query_params.applied_after or query_params.applied_before:
            date_filter = {}
            if query_params.applied_after:
                try:
                    date_filter["$gte"] = datetime.fromisoformat(query_params.applied_after)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid applied_after date format. Use YYYY-MM-DD"
                    )
            if query_params.applied_before:
                try:
                    date_filter["$lte"] = datetime.fromisoformat(query_params.applied_before)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid applied_before date format. Use YYYY-MM-DD"
                    )
            filters["applied_date"] = date_filter
        
        # Feature filters
        if query_params.has_interviews is not None:
            if query_params.has_interviews:
                filters["interviews.0"] = {"$exists": True}
            else:
                filters["interviews"] = {"$size": 0}
        
        if query_params.needs_follow_up is not None:
            if query_params.needs_follow_up:
                filters["next_follow_up"] = {"$lte": datetime.utcnow()}
            else:
                filters["next_follow_up"] = {"$gt": datetime.utcnow()}
        
        # Get applications
        applications = await ApplicationService.get_user_applications(
            user_id=str(current_user["_id"]),
            filters=filters,
            page=query_params.page,
            size=query_params.size,
            sort_by=query_params.sort_by or "created_at",
            sort_order=query_params.sort_order,
            search=query_params.search
        )
        
        # Get status counts for summary
        status_counts = await ApplicationService.get_application_status_counts(
            str(current_user["_id"])
        )
        
        return ApplicationListResponse(
            applications=applications["applications"],
            total=applications["total"],
            page=query_params.page,
            size=query_params.size,
            pages=applications["pages"],
            has_next=applications["has_next"],
            has_prev=applications["has_prev"],
            status_counts=status_counts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve applications"
        )


@router.get("/{application_id}", response_model=Application)
async def get_application(
    application_id: str,
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Get application details by ID
    """
    try:
        await track_api_usage("get_application", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        return Application(**application)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application"
        )


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: str,
    application_update: ApplicationUpdate,
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Update application
    """
    try:
        await track_api_usage("update_application", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application to check ownership
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        # Update application
        success = await ApplicationService.update_application(
            str(app_object_id),
            application_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update application"
            )
        
        # Get updated application
        updated_application = await ApplicationService.get_application_by_id(str(app_object_id))
        
        return ApplicationResponse(
            id=str(updated_application["_id"]),
            job_id=str(updated_application["job_id"]),
            user_id=str(updated_application["user_id"]),
            status=updated_application["status"],
            source=updated_application["source"],
            applied_date=updated_application.get("applied_date"),
            job_title=updated_application.get("job_title"),
            company_name=updated_application.get("company_name"),
            location=updated_application.get("location"),
            priority=updated_application["priority"],
            documents_count=len(updated_application.get("documents", [])),
            communications_count=len(updated_application.get("communications", [])),
            interviews_count=len(updated_application.get("interviews", [])),
            tasks_count=len(updated_application.get("tasks", [])),
            has_custom_cv=updated_application.get("custom_cv") is not None,
            has_cover_letter=updated_application.get("cover_letter") is not None,
            last_activity=updated_application["updated_at"],
            created_at=updated_application["created_at"],
            updated_at=updated_application["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application"
        )


@router.delete("/{application_id}", response_model=SuccessResponse)
async def delete_application(
    application_id: str,
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Delete application (soft delete)
    """
    try:
        await track_api_usage("delete_application", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application to check ownership
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        # Delete application
        success = await ApplicationService.delete_application(str(app_object_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete application"
            )
        
        return SuccessResponse(
            message="Application deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete application"
        )


@router.post("/{application_id}/cv/generate", response_model=CustomCV)
async def generate_custom_cv(
    application_id: str,
    customization_prompt: Optional[str] = None,
    current_user: Dict[str, Any] = CurrentVerifiedUser,
    limits_check: Dict[str, Any] = Depends(check_cv_generation_limits)
):
    """
    Generate custom CV for specific application using AI
    """
    try:
        await track_api_usage("generate_custom_cv", current_user)
        await check_feature_access("cv_customization", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        # Generate custom CV using AI
        custom_cv = await AIService.generate_custom_cv(
            user_id=str(current_user["_id"]),
            job_id=str(application["job_id"]),
            application_id=str(app_object_id),
            customization_prompt=customization_prompt
        )
        
        if not custom_cv:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate custom CV"
            )
        
        return CustomCV(**custom_cv)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating custom CV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate custom CV"
        )


@router.post("/{application_id}/cover-letter/generate", response_model=CoverLetter)
async def generate_cover_letter(
    application_id: str,
    tone: str = Query("professional", description="Cover letter tone"),
    custom_points: Optional[List[str]] = None,
    current_user: Dict[str, Any] = CurrentVerifiedUser,
    limits_check: Dict[str, Any] = Depends(check_cover_letter_limits)
):
    """
    Generate cover letter for specific application using AI
    """
    try:
        await track_api_usage("generate_cover_letter", current_user)
        await check_feature_access("cover_letter_generation", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        # Generate cover letter using AI
        cover_letter = await AIService.generate_cover_letter(
            user_id=str(current_user["_id"]),
            job_id=str(application["job_id"]),
            application_id=str(app_object_id),
            tone=tone,
            custom_points=custom_points or []
        )
        
        if not cover_letter:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate cover letter"
            )
        
        return CoverLetter(**cover_letter)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cover letter"
        )


@router.post("/{application_id}/auto-apply", response_model=SuccessResponse)
async def auto_apply_to_job(
    application_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = CurrentVerifiedUser,
    limits_check: Dict[str, Any] = Depends(check_auto_apply_limits)
):
    """
    Automatically apply to job using browser automation (Premium feature)
    """
    try:
        await track_api_usage("auto_apply", current_user)
        await check_feature_access("auto_application", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        # Check if application is in draft status
        if application["status"] != ApplicationStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Auto-apply only available for draft applications"
            )
        
        # Start auto-application process in background
        background_tasks.add_task(
            AutomationService.auto_apply_to_job,
            str(app_object_id),
            str(current_user["_id"])
        )
        
        # Update application status
        await ApplicationService.update_application_status(
            str(app_object_id),
            ApplicationStatus.PENDING
        )
        
        return SuccessResponse(
            message="Auto-application process started. You will be notified when complete.",
            data={"application_id": str(app_object_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting auto-apply: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start auto-application"
        )


@router.post("/{application_id}/interviews", response_model=SuccessResponse)
async def add_interview(
    application_id: str,
    interview: Interview,
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Add interview to application
    """
    try:
        await track_api_usage("add_interview", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application to check ownership
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        # Add interview
        success = await ApplicationService.add_interview(str(app_object_id), interview)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add interview"
            )
        
        return SuccessResponse(
            message="Interview added successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add interview"
        )


@router.post("/{application_id}/tasks", response_model=SuccessResponse)
async def add_task(
    application_id: str,
    task: ApplicationTask,
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Add task to application
    """
    try:
        await track_api_usage("add_task", current_user)
        
        # Validate application ID
        app_object_id = await get_valid_object_id(application_id, "application_id")
        
        # Get application to check ownership
        application = await ApplicationService.get_application_by_id(str(app_object_id))
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check ownership
        await check_user_ownership(str(application["user_id"]), current_user)
        
        # Add task
        success = await ApplicationService.add_task(str(app_object_id), task)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add task"
            )
        
        return SuccessResponse(
            message="Task added successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add task"
        )


@router.get("/stats/overview", response_model=ApplicationStats)
async def get_application_stats(
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Get user's application statistics overview
    """
    try:
        await track_api_usage("get_application_stats", current_user)
        
        # Get application statistics
        stats = await ApplicationService.get_user_application_stats(str(current_user["_id"]))
        
        return ApplicationStats(**stats)
        
    except Exception as e:
        logger.error(f"Error getting application stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application statistics"
        )


@router.get("/analytics/success-rate")
async def get_success_rate_analytics(
    period_days: int = Query(90, ge=30, le=365, description="Analysis period in days"),
    current_user: Dict[str, Any] = CurrentVerifiedUser
):
    """
    Get detailed success rate analytics
    """
    try:
        await track_api_usage("get_success_analytics", current_user)
        await check_feature_access("advanced_analytics", current_user)
        
        # Get success rate analytics
        analytics = await ApplicationService.get_success_rate_analytics(
            user_id=str(current_user["_id"]),
            period_days=period_days
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting success analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve success analytics"
        )


@router.get("/timeline")
async def get_application_timeline(
    days: int = Query(30, ge=1, le=90, description="Number of days for timeline"),
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Get application activity timeline
    """
    try:
        await track_api_usage("get_application_timeline", current_user)
        
        # Get timeline
        timeline = await ApplicationService.get_application_timeline(
            user_id=str(current_user["_id"]),
            days=days
        )
        
        return {
            "timeline": timeline,
            "period_days": days,
            "total_events": len(timeline)
        }
        
    except Exception as e:
        logger.error(f"Error getting application timeline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application timeline"
        )


@router.get("/follow-ups/needed")
async def get_follow_ups_needed(
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Get applications that need follow-up
    """
    try:
        await track_api_usage("get_follow_ups", current_user)
        
        # Get applications needing follow-up
        follow_ups = await ApplicationService.get_applications_needing_followup(
            str(current_user["_id"])
        )
        
        return {
            "applications": follow_ups,
            "count": len(follow_ups)
        }
        
    except Exception as e:
        logger.error(f"Error getting follow-ups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve follow-ups"
        )


@router.post("/bulk/update-status", response_model=SuccessResponse)
async def bulk_update_status(
    application_ids: List[str],
    new_status: ApplicationStatus,
    reason: Optional[str] = None,
    current_user: Dict[str, Any] = CurrentActiveUser
):
    """
    Bulk update application statuses
    """
    try:
        await track_api_usage("bulk_update_status", current_user)
        await check_feature_access("bulk_operations", current_user)
        
        # Validate application IDs
        valid_ids = []
        for app_id in application_ids:
            try:
                valid_ids.append(str(await get_valid_object_id(app_id, "application_id")))
            except HTTPException:
                continue  # Skip invalid IDs
        
        if not valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid application IDs provided"
            )
        
        # Bulk update
        updated_count = await ApplicationService.bulk_update_status(
            application_ids=valid_ids,
            user_id=str(current_user["_id"]),
            new_status=new_status,
            reason=reason
        )
        
        return SuccessResponse(
            message=f"Updated {updated_count} applications",
            data={"updated_count": updated_count}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk update applications"
        )


# Admin-only endpoints
@router.get("/admin/overview")
async def get_admin_applications_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days for overview"),
    current_admin: Dict[str, Any] = CurrentAdminUser
):
    """
    Get applications overview for admin dashboard
    """
    try:
        await track_api_usage("admin_applications_overview", current_admin)
        
        # Get admin overview
        overview = await ApplicationService.get_admin_applications_overview(days)
        
        return overview
        
    except Exception as e:
        logger.error(f"Error getting admin overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin overview"
        )