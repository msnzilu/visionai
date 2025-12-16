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
    Generate customized CV for specific job using CVCustomizationService
    Returns document ID of generated CV
    """
    try:
        from app.services.cv_customization_service import cv_customization_service
        
        # Prepare job data in expected format
        job_data = {
            "_id": str(job["_id"]),
            "title": job.get("title", ""),
            "company_name": job.get("company", ""),
            "description": job.get("description", ""),
            "requirements": job.get("requirements", []),
            "skills_required": job.get("skills_required", [])
        }
        
        # Generate customized CV
        result = await cv_customization_service.customize_cv_for_job(
            cv_data=user_cv,
            job_data=job_data
        )
        
        if not result.get("success"):
            logger.error(f"Failed to generate custom CV: {result.get('error')}")
            return None
            
        customized_cv = result.get("customized_cv")
        match_score = result.get("job_match_score", 0.0)
        
        # Save customized CV to database using the service's storage method
        # Note: The service has a private _store_generated_cv, but we can replicate the storage logic here
        # or expose a public store method. For now, we'll store it directly to ensure compatibility
        
        db = await get_database()
        cv_doc = {
            "user_id": user_cv.get("user_id"),
            "job_id": str(job.get("_id")),
            "type": "customized_cv",
            "content": customized_cv,
            "original_cv_id": user_cv.get("_id"),
            "match_score": match_score,
            "created_at": datetime.utcnow()
        }
        
        insert_result = await db.documents.insert_one(cv_doc)
        return str(insert_result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error generating custom CV: {e}")
        return None


async def generate_cover_letter(user_cv: Dict, job: Dict) -> str:
    """
    Generate customized cover letter for specific job using CoverLetterService
    Returns document ID of generated cover letter
    """
    try:
        from app.services.cover_letter_service import cover_letter_service
        
        # Prepare job data
        job_data = {
            "_id": str(job["_id"]),
            "title": job.get("title", ""),
            "company_name": job.get("company", ""),
            "description": job.get("description", ""),
            "requirements": job.get("requirements", []),
            "skills_required": job.get("skills_required", [])
        }
        
        # Generate cover letter
        result = await cover_letter_service.generate_cover_letter(
            cv_data=user_cv,
            job_data=job_data,
            tone="professional" # Default tone for auto-apply
        )
        
        if not result.get("success"):
            logger.error(f"Failed to generate cover letter: {result.get('error')}")
            return None
            
        cover_letter_data = result.get("cover_letter")
        
        # Extract the full text content nicely
        content_text = cover_letter_data.get("content", {}).get("full_text", "")
        
        # Save cover letter to database
        db = await get_database()
        cover_doc = {
            "user_id": user_cv.get("user_id"),
            "job_id": str(job.get("_id")),
            "type": "cover_letter",
            "content": content_text, # Store text for email sending compatibility
            "structured_content": cover_letter_data, # Store structured for future use
            "created_at": datetime.utcnow()
        }
        
        insert_result = await db.documents.insert_one(cover_doc)
        return str(insert_result.inserted_id)
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return None


async def process_auto_apply_for_user(user: Dict, db, task_instance=None) -> Dict:
    """Core logic to process auto-apply for a single user"""
    stats = {
        "jobs_found": 0,
        "jobs_analyzed": 0,
        "matches_found": 0,
        "applications_sent": 0,
        "daily_limit": 0,
        "limit_reached": False,
        "reason": ""
    }
    
    try:
        if task_instance:
            task_instance.update_state(state='PROGRESS', meta={'current': 5, 'total': 100, 'status': 'Initializing user data...'})

        user_id = str(user["_id"])
        
        # Get user's CV data
        user_cv = user.get("cv_data", {})
        if not user_cv:
            return {"success": False, "error": "No CV data found", "stats": stats}

        user_cv["user_id"] = user_id
        user_cv["full_name"] = user.get("full_name")
        
        # Get user preferences
        preferences = user.get("preferences", {})
        max_daily_applications = preferences.get("max_daily_applications", 5)
        min_match_score = preferences.get("min_match_score", 0.7)
        
        stats["daily_limit"] = max_daily_applications
        
        # Check how many applications sent today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        applications_today = await db.applications.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": today_start},
            "auto_applied": True
        })
        
        if applications_today >= max_daily_applications:
            logger.info(f"User {user_id} reached daily limit ({max_daily_applications})")
            stats["limit_reached"] = True
            stats["reason"] = f"Daily limit reached ({applications_today}/{max_daily_applications})"
            return {"success": True, "applications_sent": 0, "message": stats["reason"], "stats": stats}
        
        remaining_applications = max_daily_applications - applications_today
        
        if task_instance:
            task_instance.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Finding matching jobs...'})

        # Find new jobs (not already applied to)
        applied_job_ids = await db.applications.distinct("job_id", {"user_id": user_id})
        
        # Get jobs from last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        exclude_ids = [ObjectId(jid) for jid in applied_job_ids]
        
        # Get recommended roles from user profile
        user_profile = user.get("profile", {})
        recommended_roles = user_profile.get("recommended_roles", [])
        
        # If no roles found in profile, check cv_data as fallback
        if not recommended_roles and "recommended_roles" in user_cv:
            recommended_roles = user_cv["recommended_roles"]
            
        new_jobs = []
        
        if recommended_roles:
            logger.info(f"Searching jobs for user {user_id} using roles: {recommended_roles}")
            
            # Import job service for live scraping
            from app.services.job_service import get_job_service
            job_service = get_job_service(db)
            
            # Search for each role
            for role in recommended_roles:
                # Trigger live scrape for this role first (Consolidated Task)
                try:
                    user_location = user_profile.get("personal_info", {}).get("location") or "Remote"
                    logger.info(f"Triggering consolidated scrape for role: {role} in {user_location}")
                    
                    # Scrape fresh jobs -> database
                    await job_service.aggregate_from_sources(
                        query=role,
                        location=user_location,
                        limit=20
                    )
                except Exception as e:
                    logger.error(f"Error during consolidated scraping for {role}: {e}")

                # Now search the DB (which includes fresh jobs)
                role_jobs = await db.jobs.find({
                    "_id": {"$nin": exclude_ids + [j["_id"] for j in new_jobs]}, # Avoid duplicates
                    "is_active": True,
                    "created_at": {"$gte": seven_days_ago},
                    "email": {"$exists": True, "$ne": None},
                    "$or": [
                        {"title": {"$regex": role, "$options": "i"}},
                        {"description": {"$regex": role, "$options": "i"}}
                    ]
                }).limit(5).to_list(length=5)
                
                new_jobs.extend(role_jobs)
                
                if len(new_jobs) >= remaining_applications * 5:
                    break
        else:
            # Fallback to generic recent jobs if no roles identified
            logger.info(f"No specific roles found for user {user_id}, using generic search")
            new_jobs = await db.jobs.find({
                "_id": {"$nin": exclude_ids},
                "is_active": True,
                "created_at": {"$gte": seven_days_ago},
                "email": {"$exists": True, "$ne": None}
            }).limit(remaining_applications * 5).to_list(length=remaining_applications * 5)
        
        stats["jobs_found"] = len(new_jobs)
        
        if not new_jobs:
            logger.info(f"No new jobs for user {user_id}")
            stats["reason"] = "No new matching jobs found in database"
            return {"success": True, "applications_sent": 0, "message": stats["reason"], "stats": stats}
        
        if task_instance:
            task_instance.update_state(state='PROGRESS', meta={'current': 20, 'total': 100, 'status': f'Analyzing {len(new_jobs)} potential jobs...'})

        # Calculate match scores for all jobs
        job_scores = []
        for job in new_jobs:
            score = await calculate_job_match_score(user_cv, job)
            stats["jobs_analyzed"] += 1
            if score >= min_match_score:
                job_scores.append((job, score))
        
        stats["matches_found"] = len(job_scores)
        
        # Sort by score and take top matches
        job_scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = job_scores[:remaining_applications]
        
        if not top_matches:
             stats["reason"] = f"Analyzed {len(new_jobs)} jobs, but none met your match score criteria (> {int(min_match_score*100)}%)"
             return {"success": True, "applications_sent": 0, "message": stats["reason"], "stats": stats}

        applications_sent = 0
        total_matches = len(top_matches)
        
        # Apply to each matching job
        for idx, (job, match_score) in enumerate(top_matches):
            try:
                job_id = str(job["_id"])
                
                # Calculate progress based on iteration
                base_progress = 30
                progress_step = 60 / total_matches # Distribute remaining 60% among matches
                current_base = base_progress + (idx * progress_step)
                
                if task_instance:
                    task_instance.update_state(state='PROGRESS', meta={
                        'current': int(current_base), 
                        'total': 100, 
                        'status': f'Applying to {job.get("title")} (Generating CV)...'
                    })

                logger.info(f"Auto-applying to {job.get('title')} at {job.get('company')} (score: {match_score})")
                
                # Generate custom CV
                custom_cv_id = await generate_custom_cv(user_cv, job)
                if not custom_cv_id:
                    logger.error(f"Failed to generate CV for job {job_id}")
                    continue
                
                if task_instance:
                    task_instance.update_state(state='PROGRESS', meta={
                        'current': int(current_base + (progress_step * 0.5)), 
                        'total': 100, 
                        'status': f'Applying to {job.get("title")} (Writing Cover Letter)...'
                    })

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
                
                if task_instance:
                    task_instance.update_state(state='PROGRESS', meta={
                        'current': int(current_base + (progress_step * 0.9)), 
                        'total': 100, 
                        'status': f'Sending application to {job.get("company")}...'
                    })

                # Send application via email agent
                # Extract rich form data using the shared service for consistency with Quick Apply
                form_data = await email_agent_service.extract_form_data_from_cv(user_id, cv_data=user_cv)
                
                # Add the specific message for this application
                form_data["message"] = f"Please find attached my CV and cover letter for the {job.get('title')} position."
                
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
                
                applications_sent += 1
                stats["applications_sent"] += 1
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
        
        if task_instance:
            task_instance.update_state(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'Test run complete!'})

        msg = f"Sent {applications_sent} applications."
        if applications_sent == 0:
             msg = "No applications sent."
             if stats["reason"]:
                 msg = stats["reason"]

        return {"success": True, "applications_sent": applications_sent, "message": msg, "stats": stats}

    except Exception as e:
        logger.error(f"Error processing user {user.get('_id')}: {e}")
        return {"success": False, "error": str(e), "stats": stats}


@celery_app.task(name="app.workers.auto_apply.auto_apply_to_matching_jobs")
def auto_apply_to_matching_jobs():
    """
    FULL AUTOMATION: Find matching jobs and automatically apply
    Runs every 6 hours
    """
    async def _auto_apply():
        try:
            db = await get_database()
            
            # Get users with auto-apply enabled
            auto_apply_users = await db.users.find({
                "preferences.auto_apply_enabled": True,
                "gmail_auth": {"$exists": True, "$ne": None},
                "cv_data": {"$exists": True, "$ne": None}
            }).to_list(length=None)
            
            if not auto_apply_users:
                logger.info("No users with auto-apply enabled")
                return {"success": True, "applications": 0}
            
            total_applications = 0
            
            for user in auto_apply_users:
                # No task instance passed for batch job (or we could bind it too if needed later)
                result = await process_auto_apply_for_user(user, db)
                if result.get("success"):
                    total_applications += result.get("applications_sent", 0)
            
            logger.info(f"Auto-applied to {total_applications} jobs")
            return {"success": True, "applications": total_applications}
            
        except Exception as e:
            logger.error(f"Error in auto_apply_to_matching_jobs: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_auto_apply())


@celery_app.task(bind=True, name="app.workers.auto_apply.trigger_single_user_test")
def trigger_single_user_test(self, user_id: str):
    """
    Trigger a single test run for a specific user.
    Calculates matches and applies to jobs immediately.
    """
    async def _run_test():
        try:
            db = await get_database()
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "error": "User not found"}
            
            return await process_auto_apply_for_user(user, db, task_instance=self)
            
        except Exception as e:
            logger.error(f"Error in single user test: {e}")
            return {"success": False, "error": str(e)}

    return run_async(_run_test())


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
