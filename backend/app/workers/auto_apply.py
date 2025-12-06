# backend/app/workers/auto_apply.py
"""
Automatic Job Application Worker
Fully automated job application without user intervention
"""

from app.workers.celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.email_agent_service import email_agent_service
import asyncio
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from typing import List, Dict, Any
import openai

logger = logging.getLogger(__name__)


async def get_database():
    """Get database connection"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    return client[settings.DATABASE_NAME]


def run_async(coro):
    """Helper to run async functions in Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def calculate_job_match_score(user_cv: Dict, job: Dict) -> float:
    """
    Calculate match score between user CV and job using AI
    Returns score from 0.0 to 1.0
    """
    try:
        openai.api_key = settings.OPENAI_API_KEY
        
        # Extract key info from CV
        cv_skills = user_cv.get("skills", [])
        cv_experience = user_cv.get("experience", [])
        cv_education = user_cv.get("education", [])
        
        # Extract job requirements
        job_title = job.get("title", "")
        job_description = job.get("description", "")
        job_requirements = job.get("requirements", "")
        
        # Use OpenAI to calculate match
        prompt = f"""
        Analyze the match between this candidate and job. Return ONLY a number between 0.0 and 1.0.
        
        Candidate Skills: {', '.join(cv_skills[:10])}
        Candidate Experience: {len(cv_experience)} years
        
        Job Title: {job_title}
        Job Requirements: {job_requirements[:500]}
        
        Match Score (0.0-1.0):
        """
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.3
        )
        
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
        
    except Exception as e:
        logger.error(f"Error calculating match score: {e}")
        return 0.0


async def generate_custom_cv(user_cv: Dict, job: Dict) -> str:
    """
    Generate customized CV for specific job using AI
    Returns document ID of generated CV
    """
    try:
        openai.api_key = settings.OPENAI_API_KEY
        
        # Use OpenAI to customize CV
        prompt = f"""
        Customize this CV for the following job. Keep it professional and ATS-friendly.
        
        Original CV:
        Name: {user_cv.get('full_name')}
        Skills: {', '.join(user_cv.get('skills', []))}
        Experience: {user_cv.get('experience_summary', '')}
        
        Target Job:
        Title: {job.get('title')}
        Company: {job.get('company')}
        Requirements: {job.get('requirements', '')[:500]}
        
        Generate a customized CV summary (2-3 paragraphs):
        """
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        customized_content = response.choices[0].message.content.strip()
        
        # Save customized CV to database
        db = await get_database()
        cv_doc = {
            "user_id": user_cv.get("user_id"),
            "job_id": str(job.get("_id")),
            "type": "customized_cv",
            "content": customized_content,
            "original_cv_id": user_cv.get("_id"),
            "created_at": datetime.utcnow()
        }
        
        result = await db.documents.insert_one(cv_doc)
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error generating custom CV: {e}")
        return None


async def generate_cover_letter(user_cv: Dict, job: Dict) -> str:
    """
    Generate customized cover letter for specific job using AI
    Returns document ID of generated cover letter
    """
    try:
        openai.api_key = settings.OPENAI_API_KEY
        
        prompt = f"""
        Write a professional cover letter for this job application.
        
        Candidate:
        Name: {user_cv.get('full_name')}
        Skills: {', '.join(user_cv.get('skills', [])[:5])}
        Experience: {user_cv.get('experience_summary', '')}
        
        Job:
        Title: {job.get('title')}
        Company: {job.get('company')}
        Description: {job.get('description', '')[:500]}
        
        Write a compelling cover letter (3-4 paragraphs):
        """
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        
        cover_letter_content = response.choices[0].message.content.strip()
        
        # Save cover letter to database
        db = await get_database()
        cover_doc = {
            "user_id": user_cv.get("user_id"),
            "job_id": str(job.get("_id")),
            "type": "cover_letter",
            "content": cover_letter_content,
            "created_at": datetime.utcnow()
        }
        
        result = await db.documents.insert_one(cover_doc)
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return None


@celery_app.task(name="app.workers.auto_apply.auto_apply_to_matching_jobs")
def auto_apply_to_matching_jobs():
    """
    FULL AUTOMATION: Find matching jobs and automatically apply
    Runs every 6 hours
    
    Process:
    1. Get all users with auto-apply enabled
    2. For each user, find matching jobs
    3. Generate custom CV and cover letter
    4. Automatically submit application
    5. Start tracking
    """
    async def _auto_apply():
        try:
            db = await get_database()
            
            # Get users with auto-apply enabled
            auto_apply_users = await db.users.find({
                "preferences.auto_apply_enabled": True,
                "gmail_auth": {"$exists": True, "$ne": None},
                "cv_parsed": {"$exists": True, "$ne": None}
            }).to_list(length=None)
            
            if not auto_apply_users:
                logger.info("No users with auto-apply enabled")
                return {"success": True, "applications": 0}
            
            total_applications = 0
            
            for user in auto_apply_users:
                try:
                    user_id = str(user["_id"])
                    
                    # Get user's CV data
                    user_cv = user.get("cv_parsed", {})
                    user_cv["user_id"] = user_id
                    user_cv["full_name"] = user.get("full_name")
                    
                    # Get user preferences
                    preferences = user.get("preferences", {})
                    max_daily_applications = preferences.get("max_daily_applications", 5)
                    min_match_score = preferences.get("min_match_score", 0.7)
                    
                    # Check how many applications sent today
                    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    applications_today = await db.applications.count_documents({
                        "user_id": user_id,
                        "created_at": {"$gte": today_start},
                        "auto_applied": True
                    })
                    
                    if applications_today >= max_daily_applications:
                        logger.info(f"User {user_id} reached daily limit ({max_daily_applications})")
                        continue
                    
                    remaining_applications = max_daily_applications - applications_today
                    
                    # Find new jobs (not already applied to)
                    applied_job_ids = await db.applications.distinct("job_id", {"user_id": user_id})
                    
                    # Get jobs from last 7 days
                    seven_days_ago = datetime.utcnow() - timedelta(days=7)
                    new_jobs = await db.jobs.find({
                        "_id": {"$nin": [ObjectId(jid) for jid in applied_job_ids]},
                        "is_active": True,
                        "created_at": {"$gte": seven_days_ago},
                        "email": {"$exists": True, "$ne": None}  # Must have email to apply
                    }).limit(remaining_applications * 2).to_list(length=remaining_applications * 2)
                    
                    if not new_jobs:
                        logger.info(f"No new jobs for user {user_id}")
                        continue
                    
                    # Calculate match scores for all jobs
                    job_scores = []
                    for job in new_jobs:
                        score = await calculate_job_match_score(user_cv, job)
                        if score >= min_match_score:
                            job_scores.append((job, score))
                    
                    # Sort by score and take top matches
                    job_scores.sort(key=lambda x: x[1], reverse=True)
                    top_matches = job_scores[:remaining_applications]
                    
                    # Apply to each matching job
                    for job, match_score in top_matches:
                        try:
                            job_id = str(job["_id"])
                            
                            logger.info(f"Auto-applying to {job.get('title')} at {job.get('company')} (score: {match_score})")
                            
                            # Generate custom CV
                            custom_cv_id = await generate_custom_cv(user_cv, job)
                            if not custom_cv_id:
                                logger.error(f"Failed to generate CV for job {job_id}")
                                continue
                            
                            # Generate cover letter
                            cover_letter_id = await generate_cover_letter(user_cv, job)
                            if not cover_letter_id:
                                logger.error(f"Failed to generate cover letter for job {job_id}")
                                continue
                            
                            # Create application record
                            application = {
                                "user_id": user_id,
                                "job_id": job_id,
                                "job_title": job.get("title"),
                                "company_name": job.get("company"),
                                "status": "submitted",
                                "source": "auto_apply",
                                "auto_applied": True,
                                "match_score": match_score,
                                "cv_document_id": custom_cv_id,
                                "cover_letter_document_id": cover_letter_id,
                                "created_at": datetime.utcnow(),
                                "timeline": [{
                                    "status": "submitted",
                                    "timestamp": datetime.utcnow(),
                                    "note": f"Auto-applied (match score: {match_score:.2f})"
                                }]
                            }
                            
                            result = await db.applications.insert_one(application)
                            application_id = str(result.inserted_id)
                            
                            # Send application via email agent
                            form_data = {
                                "full_name": user.get("full_name"),
                                "email": user.get("email"),
                                "phone": user_cv.get("phone", ""),
                                "message": f"Please find attached my CV and cover letter for the {job.get('title')} position."
                            }
                            
                            # Queue email sending
                            from app.workers.email_sender import send_application_email
                            send_application_email.delay(
                                user_id=user_id,
                                job_id=job_id,
                                application_id=application_id,
                                recipient_email=job.get("email"),
                                form_data=form_data,
                                cv_document_id=custom_cv_id,
                                cover_letter_document_id=cover_letter_id,
                                additional_message=None
                            )
                            
                            total_applications += 1
                            logger.info(f"Successfully auto-applied to job {job_id}")
                            
                            # Notify user about auto-application
                            from app.workers.email_campaigns import send_status_notification
                            send_status_notification.delay(
                                application_id,
                                "draft",
                                "submitted"
                            )
                            
                        except Exception as e:
                            logger.error(f"Error auto-applying to job {job.get('_id')}: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"Error processing user {user.get('_id')}: {e}")
                    continue
            
            logger.info(f"Auto-applied to {total_applications} jobs")
            return {"success": True, "applications": total_applications}
            
        except Exception as e:
            logger.error(f"Error in auto_apply_to_matching_jobs: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_auto_apply())


@celery_app.task(name="app.workers.auto_apply.enable_auto_apply_for_user")
def enable_auto_apply_for_user(user_id: str, max_daily_applications: int = 5, min_match_score: float = 0.7):
    """
    Enable auto-apply for a specific user
    Can be called from API when user opts in
    """
    async def _enable():
        try:
            db = await get_database()
            
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "preferences.auto_apply_enabled": True,
                    "preferences.max_daily_applications": max_daily_applications,
                    "preferences.min_match_score": min_match_score,
                    "preferences.auto_apply_enabled_at": datetime.utcnow()
                }}
            )
            
            logger.info(f"Auto-apply enabled for user {user_id}")
            return {"success": True, "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Error enabling auto-apply: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_enable())
