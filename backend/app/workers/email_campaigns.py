# backend/app/workers/email_campaigns.py
"""
Email Campaign Worker - Automated Customer Journey
Handles all automated email communications throughout the job search journey
"""

from app.workers.celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.gmail_service import gmail_service
import asyncio
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from typing import List, Dict, Any

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


async def send_email_via_gmail(user, subject: str, body: str):
    """Helper function to send email via Gmail"""
    try:
        gmail_auth = user.get("gmail_auth")
        if not gmail_auth:
            logger.warning(f"User {user.get('_id')} has no Gmail connected, cannot send email")
            return False
        
        from app.models.user import GmailAuth
        auth = GmailAuth(**gmail_auth)
        
        gmail_service.send_email(
            auth=auth,
            to=user.get("email"),
            subject=subject,
            body=body
        )
        return True
    except Exception as e:
        logger.error(f"Error sending email to {user.get('email')}: {e}")
        return False


@celery_app.task(name="app.workers.email_campaigns.send_daily_job_digest")
def send_daily_job_digest():
    """
    Send daily email digest with top job matches to active users
    Runs every day at 9 AM
    """
    async def _send_digest():
        try:
            db = await get_database()
            
            # Get active users (logged in within last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_users = await db.users.find({
                "last_login": {"$gte": thirty_days_ago},
                "email_verified": True,
                "preferences.daily_digest": {"$ne": False}  # Not opted out
            }).to_list(length=None)
            
            sent_count = 0
            for user in active_users:
                try:
                    user_id = str(user["_id"])
                    
                    # Find matching jobs
                    jobs = await db.jobs.find({
                        "is_active": True,
                        "created_at": {"$gte": datetime.utcnow() - timedelta(days=3)},
                    }).limit(5).to_list(length=5)
                    
                    if not jobs:
                        continue
                    
                    # Get application stats
                    stats = await db.applications.aggregate([
                        {"$match": {"user_id": user_id}},
                        {"$group": {
                            "_id": "$status",
                            "count": {"$sum": 1}
                        }}
                    ]).to_list(length=None)
                    
                    total_apps = sum(s["count"] for s in stats)
                    
                    # Compose email body
                    job_list = "\n\n".join([
                        f"• {job.get('title')} at {job.get('company')}\n  Location: {job.get('location', 'Remote')}\n  Apply: {settings.FRONTEND_URL}/jobs/{job.get('_id')}"
                        for job in jobs
                    ])
                    
                    email_body = f"""Hi {user.get('full_name', 'there')},

Here are your top 5 job matches for today ({datetime.utcnow().strftime('%B %d, %Y')}):

{job_list}

Your Stats:
- Total Applications: {total_apps}
- Active Applications: {len([s for s in stats if s['_id'] not in ['rejected', 'withdrawn']])}

View all jobs: {settings.FRONTEND_URL}/jobs

Happy job hunting!
Vision.AI Team"""
                    
                    # Send email
                    success = await send_email_via_gmail(
                        user,
                        subject=f"Your Daily Job Digest - {len(jobs)} New Matches",
                        body=email_body
                    )
                    
                    if success:
                        sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Error sending digest to user {user.get('_id')}: {e}")
                    continue
            
            logger.info(f"Sent {sent_count} job digest emails")
            return {"success": True, "sent": sent_count}
            
        except Exception as e:
            logger.error(f"Error in send_daily_job_digest: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_send_digest())


@celery_app.task(name="app.workers.email_campaigns.send_welcome_email")
def send_welcome_email(user_id: str):
    """
    Send welcome email to new user
    Triggered immediately after signup
    """
    async def _send_welcome():
        try:
            db = await get_database()
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Compose welcome email
            email_body = f"""Welcome to Vision.AI, {user.get('full_name', 'there')}!

We're excited to help you automate your job search. Here's what happens next:

1. Upload your CV (we'll parse it automatically)
2. Set your job preferences
3. We'll start matching you with jobs
4. Apply with one click!

Get started: {settings.FRONTEND_URL}/profile

If you have any questions, reply to this email or visit our help center.

Best regards,
The Vision.AI Team"""
            
            # Send email
            success = await send_email_via_gmail(
                user,
                subject="Welcome to Vision.AI - Let's Get Started!",
                body=email_body
            )
            
            # Mark welcome email as sent
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"welcome_email_sent": True, "welcome_email_sent_at": datetime.utcnow()}}
            )
            
            return {"success": success, "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_send_welcome())


@celery_app.task(name="app.workers.email_campaigns.send_interview_reminder")
def send_interview_reminder(application_id: str, hours_before: int = 24):
    """
    Send interview reminder email
    Triggered 24 hours and 1 hour before interview
    """
    async def _send_reminder():
        try:
            db = await get_database()
            app = await db.applications.find_one({"_id": ObjectId(application_id)})
            
            if not app:
                return {"success": False, "error": "Application not found"}
            
            user = await db.users.find_one({"_id": ObjectId(app["user_id"])})
            interview = app.get("interviews", [{}])[0] if app.get("interviews") else None
            
            if not interview:
                return {"success": False, "error": "No interview found"}
            
            # Compose reminder email
            email_body = f"""Interview Reminder - {app.get('job_title')} at {app.get('company_name')}

Your interview is in {hours_before} hours!

Interview Details:
- Date: {interview.get('scheduled_date')}
- Type: {interview.get('type', 'Not specified')}
- Location: {interview.get('location', 'Not specified')}

Preparation Tips:
✓ Research the company
✓ Review the job description
✓ Prepare STAR method examples
✓ Test your tech setup (if video call)
✓ Prepare questions to ask

View application: {settings.FRONTEND_URL}/applications/{application_id}

Good luck!
Vision.AI Team"""
            
            # Send email
            success = await send_email_via_gmail(
                user,
                subject=f"Interview Reminder: {app.get('job_title')} in {hours_before}h",
                body=email_body
            )
            
            return {"success": success, "application_id": application_id}
            
        except Exception as e:
            logger.error(f"Error sending interview reminder: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_send_reminder())


@celery_app.task(name="app.workers.email_campaigns.send_thank_you_prompt")
def send_thank_you_prompt(application_id: str):
    """
    Send thank-you email template to user after interview
    User can approve and send
    """
    async def _send_prompt():
        try:
            db = await get_database()
            app = await db.applications.find_one({"_id": ObjectId(application_id)})
            
            if not app:
                return {"success": False, "error": "Application not found"}
            
            user = await db.users.find_one({"_id": ObjectId(app["user_id"])})
            
            # Generate thank-you email template
            thank_you_template = f"""Dear Hiring Manager,

Thank you for taking the time to interview me for the {app.get('job_title')} position at {app.get('company_name')}. 

I enjoyed learning more about the role and your team. I'm very excited about the opportunity to contribute to [specific project/goal discussed].

I believe my experience in [relevant skills] would be a great fit for this position, and I'm eager to bring my expertise to your team.

Please let me know if you need any additional information from me. I look forward to hearing from you.

Best regards,
{user.get('full_name')}"""
            
            # Save template to application
            await db.applications.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {
                    "thank_you_template": thank_you_template,
                    "thank_you_template_generated_at": datetime.utcnow()
                }}
            )
            
            # Send notification to user
            email_body = f"""Hi {user.get('full_name')},

Great job on your interview for {app.get('job_title')} at {app.get('company_name')}!

We've prepared a thank-you email template for you. Review and send it from your dashboard:

{settings.FRONTEND_URL}/applications/{application_id}

Sending a thank-you email within 24 hours can significantly improve your chances!

Best regards,
Vision.AI Team"""
            
            success = await send_email_via_gmail(
                user,
                subject=f"Send Your Thank-You Email - {app.get('job_title')}",
                body=email_body
            )
            
            return {"success": success, "application_id": application_id, "template": thank_you_template}
            
        except Exception as e:
            logger.error(f"Error generating thank-you template: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_send_prompt())


@celery_app.task(name="app.workers.email_campaigns.send_status_notification")
def send_status_notification(application_id: str, old_status: str, new_status: str):
    """
    Notify user when application status changes
    Triggered by email monitoring or manual update
    """
    async def _send_notification():
        try:
            db = await get_database()
            app = await db.applications.find_one({"_id": ObjectId(application_id)})
            
            if not app:
                return {"success": False, "error": "Application not found"}
            
            user = await db.users.find_one({"_id": ObjectId(app["user_id"])})
            
            # Determine next action based on status
            next_actions = {
                "interview_scheduled": "Prepare for your interview",
                "offer_received": "Review the offer and consider negotiation",
                "rejected": "Keep applying - the right opportunity is out there!",
                "under_review": "Sit tight - they're reviewing your application"
            }
            
            next_action = next_actions.get(new_status, "Check your dashboard for updates")
            
            # Compose notification email
            email_body = f"""Application Status Update

Your application for {app.get('job_title')} at {app.get('company_name')} has been updated:

Previous Status: {old_status.replace('_', ' ').title()}
New Status: {new_status.replace('_', ' ').title()}

Next Step: {next_action}

View Details: {settings.FRONTEND_URL}/applications/{application_id}

Best regards,
Vision.AI Team"""
            
            # Send email
            success = await send_email_via_gmail(
                user,
                subject=f"Status Update: {app.get('job_title')} - {new_status.replace('_', ' ').title()}",
                body=email_body
            )
            
            # Create notification in database
            await db.notifications.insert_one({
                "user_id": app["user_id"],
                "type": "application_status_change",
                "title": f"Status Update: {app.get('job_title')}",
                "message": f"Your application status changed to {new_status.replace('_', ' ').title()}",
                "application_id": application_id,
                "created_at": datetime.utcnow(),
                "is_read": False
            })
            
            return {"success": success, "application_id": application_id}
            
        except Exception as e:
            logger.error(f"Error sending status notification: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_send_notification())


@celery_app.task(name="app.workers.email_campaigns.send_weekly_summary")
def send_weekly_summary(user_id: str = None):
    """
    Send weekly summary email to users
    Runs every Monday at 10 AM
    """
    async def _send_summary():
        try:
            db = await get_database()
            
            # Get users to send summary to
            if user_id:
                users = [await db.users.find_one({"_id": ObjectId(user_id)})]
            else:
                users = await db.users.find({
                    "email_verified": True,
                    "preferences.weekly_summary": {"$ne": False}
                }).to_list(length=None)
            
            sent_count = 0
            for user in users:
                try:
                    uid = str(user["_id"])
                    
                    # Get stats for last 7 days
                    seven_days_ago = datetime.utcnow() - timedelta(days=7)
                    
                    applications_this_week = await db.applications.count_documents({
                        "user_id": uid,
                        "created_at": {"$gte": seven_days_ago}
                    })
                    
                    interviews_this_week = await db.applications.count_documents({
                        "user_id": uid,
                        "status": "interview_scheduled",
                        "updated_at": {"$gte": seven_days_ago}
                    })
                    
                    offers_this_week = await db.applications.count_documents({
                        "user_id": uid,
                        "status": "offer_received",
                        "updated_at": {"$gte": seven_days_ago}
                    })
                    
                    # Compose summary email
                    email_body = f"""Your Weekly Job Search Summary

Hi {user.get('full_name', 'there')},

Here's your job search progress for the week:

📊 This Week:
- Applications Submitted: {applications_this_week}
- Interviews Scheduled: {interviews_this_week}
- Offers Received: {offers_this_week}

Keep up the great work!

View Dashboard: {settings.FRONTEND_URL}/dashboard

Best regards,
Vision.AI Team"""
                    
                    # Send email
                    success = await send_email_via_gmail(
                        user,
                        subject="Your Weekly Job Search Summary",
                        body=email_body
                    )
                    
                    if success:
                        sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Error sending summary to user {user.get('_id')}: {e}")
                    continue
            
            logger.info(f"Sent {sent_count} weekly summary emails")
            return {"success": True, "sent": sent_count}
            
        except Exception as e:
            logger.error(f"Error in send_weekly_summary: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_send_summary())


@celery_app.task(name="app.workers.email_campaigns.send_follow_up_reminder")
def send_follow_up_reminder(application_id: str):
    """
    Send reminder to follow up on application
    Triggered 1 week after interview with no response
    """
    async def _send_reminder():
        try:
            db = await get_database()
            app = await db.applications.find_one({"_id": ObjectId(application_id)})
            
            if not app:
                return {"success": False, "error": "Application not found"}
            
            user = await db.users.find_one({"_id": ObjectId(app["user_id"])})
            
            # Generate follow-up email template
            follow_up_template = f"""Dear Hiring Manager,

I wanted to follow up on my interview for the {app.get('job_title')} position at {app.get('company_name')}.

I remain very interested in this opportunity and would appreciate any updates on the hiring process.

Please let me know if you need any additional information from me.

Thank you for your time and consideration.

Best regards,
{user.get('full_name')}"""
            
            # Save template
            await db.applications.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": {
                    "follow_up_template": follow_up_template,
                    "follow_up_reminder_sent_at": datetime.utcnow()
                }}
            )
            
            # Send notification to user
            email_body = f"""Hi {user.get('full_name')},

It's been a week since your interview for {app.get('job_title')} at {app.get('company_name')}.

We've prepared a follow-up email template for you. Review and send it from your dashboard:

{settings.FRONTEND_URL}/applications/{application_id}

Following up shows continued interest and can help move your application forward!

Best regards,
Vision.AI Team"""
            
            success = await send_email_via_gmail(
                user,
                subject=f"Time to Follow Up - {app.get('job_title')}",
                body=email_body
            )
            
            return {"success": success, "application_id": application_id, "template": follow_up_template}
            
        except Exception as e:
            logger.error(f"Error generating follow-up template: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_send_reminder())
