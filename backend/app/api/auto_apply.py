# backend/app/api/auto_apply.py
"""
Auto-Apply API Endpoints
Premium feature for automatic job applications
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from app.api.deps import get_current_user
from app.database import get_database
from app.models.user import User
from app.workers.auto_apply import (
    enable_auto_apply_for_user,
    calculate_job_match_score
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auto-apply"])


def require_premium(user: dict) -> bool:
    """Check if user has premium subscription"""
    subscription_tier = user.get("subscription_tier", "free")
    if subscription_tier not in ["basic", "premium"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required for auto-apply feature"
        )
    return True


@router.get("/status")
async def get_auto_apply_status(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get auto-apply status and settings for current user
    """
    preferences = current_user.get("preferences", {})
    
    return {
        "enabled": preferences.get("auto_apply_enabled", False),
        "max_daily_applications": preferences.get("max_daily_applications", 5),
        "min_match_score": preferences.get("min_match_score", 0.7),
        "subscription_tier": current_user.get("subscription_tier", "free"),
        "is_premium": current_user.get("subscription_tier") in ["basic", "premium"]
    }


@router.post("/enable")
async def enable_auto_apply(
    max_daily_applications: int = 5,
    min_match_score: float = 0.7,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Enable auto-apply for current user (Premium only)
    """
    require_premium(current_user)
    
    # Validate inputs
    if max_daily_applications < 1 or max_daily_applications > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max daily applications must be between 1 and 10"
        )
    
    if min_match_score < 0.5 or min_match_score > 0.9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Min match score must be between 0.5 and 0.9"
        )
    
    # Enable auto-apply
    user_id = str(current_user["_id"])
    enable_auto_apply_for_user.delay(user_id, max_daily_applications, min_match_score)
    
    return {
        "success": True,
        "message": "Auto-apply enabled successfully",
        "settings": {
            "max_daily_applications": max_daily_applications,
            "min_match_score": min_match_score
        }
    }


@router.post("/disable")
async def disable_auto_apply(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Disable auto-apply for current user
    """
    users_collection = db["users"]
    
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "preferences.auto_apply_enabled": False,
            "preferences.auto_apply_disabled_at": datetime.utcnow()
        }}
    )
    
    return {
        "success": True,
        "message": "Auto-apply disabled successfully"
    }


@router.get("/stats")
async def get_auto_apply_stats(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get auto-apply statistics for current user
    """
    user_id = str(current_user["_id"])
    applications_collection = db["applications"]
    
    # Get today's auto-applications
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_applications = await applications_collection.count_documents({
        "user_id": user_id,
        "auto_applied": True,
        "created_at": {"$gte": today_start}
    })
    
    # Get total auto-applications
    total_applications = await applications_collection.count_documents({
        "user_id": user_id,
        "auto_applied": True
    })
    
    # Get average match score
    pipeline = [
        {"$match": {"user_id": user_id, "auto_applied": True, "match_score": {"$exists": True}}},
        {"$group": {"_id": None, "avg_score": {"$avg": "$match_score"}}}
    ]
    avg_result = await applications_collection.aggregate(pipeline).to_list(length=1)
    avg_match_score = avg_result[0]["avg_score"] if avg_result else 0
    
    # Get interview rate
    total_auto_apps = await applications_collection.count_documents({
        "user_id": user_id,
        "auto_applied": True
    })
    
    interviews = await applications_collection.count_documents({
        "user_id": user_id,
        "auto_applied": True,
        "status": {"$in": ["interview_scheduled", "interview_completed"]}
    })
    
    interview_rate = (interviews / total_auto_apps) if total_auto_apps > 0 else 0
    
    # Get preferences
    preferences = current_user.get("preferences", {})
    
    return {
        "today_applications": today_applications,
        "total_applications": total_applications,
        "avg_match_score": round(avg_match_score, 2),
        "interview_rate": round(interview_rate, 2),
        "daily_limit": preferences.get("max_daily_applications", 5),
        "remaining_today": max(0, preferences.get("max_daily_applications", 5) - today_applications)
    }


@router.get("/cv-data")
async def get_cv_data(
    current_user: dict = Depends(get_current_user)
):
    """
    Get parsed CV data for current user
    """
    cv_parsed = current_user.get("cv_parsed", {})
    
    return {
        "full_name": current_user.get("full_name", ""),
        "email": current_user.get("email", ""),
        "phone": cv_parsed.get("phone", ""),
        "location": cv_parsed.get("location", ""),
        "years_of_experience": cv_parsed.get("years_of_experience", 0),
        "education_level": cv_parsed.get("education_level", ""),
        "current_role": cv_parsed.get("current_role", ""),
        "skills": cv_parsed.get("skills", []),
        "summary": cv_parsed.get("summary", ""),
        "experience": cv_parsed.get("experience", []),
        "education": cv_parsed.get("education", [])
    }


@router.get("/matching-jobs")
async def get_matching_jobs(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get jobs matching user's CV with AI-calculated scores
    """
    user_id = str(current_user["_id"])
    cv_parsed = current_user.get("cv_parsed", {})
    
    if not cv_parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload your CV first"
        )
    
    # Get jobs user hasn't applied to
    applications_collection = db["applications"]
    applied_job_ids = await applications_collection.distinct("job_id", {"user_id": user_id})
    
    # Get recent active jobs
    jobs_collection = db["jobs"]
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    jobs = await jobs_collection.find({
        "_id": {"$nin": [ObjectId(jid) for jid in applied_job_ids if ObjectId.is_valid(jid)]},
        "is_active": True,
        "created_at": {"$gte": seven_days_ago}
    }).limit(limit * 2).to_list(length=limit * 2)
    
    # Calculate match scores for each job
    user_cv = {
        "user_id": user_id,
        "full_name": current_user.get("full_name"),
        "skills": cv_parsed.get("skills", []),
        "experience": cv_parsed.get("experience", []),
        "education": cv_parsed.get("education", []),
        "years_of_experience": cv_parsed.get("years_of_experience", 0)
    }
    
    jobs_with_scores = []
    for job in jobs:
        # Simple match score calculation (can be enhanced with AI)
        score = await calculate_simple_match_score(user_cv, job)
        
        jobs_with_scores.append({
            "_id": str(job["_id"]),
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "salary": job.get("salary", ""),
            "description": job.get("description", ""),
            "requirements": job.get("requirements", ""),
            "created_at": job.get("created_at"),
            "match_score": score,
            "applied": False
        })
    
    # Sort by match score
    jobs_with_scores.sort(key=lambda x: x["match_score"], reverse=True)
    
    return jobs_with_scores[:limit]


async def calculate_simple_match_score(user_cv: dict, job: dict) -> float:
    """
    Simple match score calculation based on skills overlap
    Can be enhanced with OpenAI for better accuracy
    """
    user_skills = set([s.lower() for s in user_cv.get("skills", [])])
    
    # Extract skills from job description and requirements
    job_text = (job.get("description", "") + " " + job.get("requirements", "")).lower()
    
    # Count skill matches
    matches = sum(1 for skill in user_skills if skill in job_text)
    total_skills = len(user_skills)
    
    if total_skills == 0:
        return 0.5  # Default score if no skills
    
    # Calculate base score
    base_score = matches / total_skills
    
    # Adjust for experience level
    required_exp = job.get("experience_years", 0)
    user_exp = user_cv.get("years_of_experience", 0)
    
    if required_exp > 0:
        exp_match = min(user_exp / required_exp, 1.5) / 1.5
        base_score = (base_score + exp_match) / 2
    
    # Clamp between 0 and 1
    return min(max(base_score, 0.0), 1.0)


@router.put("/settings")
async def update_auto_apply_settings(
    max_daily_applications: Optional[int] = None,
    min_match_score: Optional[float] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Update auto-apply settings
    """
    require_premium(current_user)
    
    update_data = {}
    
    if max_daily_applications is not None:
        if max_daily_applications < 1 or max_daily_applications > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max daily applications must be between 1 and 10"
            )
        update_data["preferences.max_daily_applications"] = max_daily_applications
    
    if min_match_score is not None:
        if min_match_score < 0.5 or min_match_score > 0.9:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Min match score must be between 0.5 and 0.9"
            )
        update_data["preferences.min_match_score"] = min_match_score
    
    if update_data:
        users_collection = db["users"]
        await users_collection.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
    
    return {
        "success": True,
        "message": "Settings updated successfully",
        "settings": {
            "max_daily_applications": max_daily_applications,
            "min_match_score": min_match_score
        }
    }
