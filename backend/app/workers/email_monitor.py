# backend/app/workers/email_monitor.py
"""
Celery Worker for Email Monitoring
Automatically scans user inboxes for application responses
"""

from app.workers.celery_app import celery_app
from app.services.email_intelligence import EmailIntelligenceService
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import asyncio
import logging
from datetime import datetime, timedelta

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


@celery_app.task(name="app.workers.email_monitor.scan_all_inboxes")
def scan_all_inboxes():
    """
    Scan all users' Gmail inboxes for application responses
    Runs every 30 minutes via Celery Beat
    """
    async def _scan():
        try:
            db = await get_database()
            email_service = EmailIntelligenceService(db)
            
            # Get all users with Gmail connected and active applications
            users_with_gmail = await db.users.find(
                {"gmail_auth": {"$exists": True, "$ne": None}},
                {"_id": 1, "email": 1}
            ).to_list(length=None)
            
            if not users_with_gmail:
                logger.info("No users with Gmail connected")
                return {"success": True, "scanned": 0, "updated": 0}
            
            scanned_count = 0
            updated_count = 0
            error_count = 0
            
            for user in users_with_gmail:
                try:
                    user_id = str(user["_id"])
                    
                    # Check if user has active applications
                    active_apps_count = await db.applications.count_documents({
                        "user_id": user_id,
                        "email_thread_id": {"$exists": True, "$ne": None},
                        "status": {
                            "$nin": [
                                "rejected",
                                "offer_accepted",
                                "withdrawn",
                                "archived"
                            ]
                        }
                    })
                    
                    if active_apps_count == 0:
                        logger.debug(f"User {user_id} has no active applications to monitor")
                        continue
                    
                    # Scan inbox for this user
                    logger.info(f"Scanning inbox for user {user_id} ({active_apps_count} active applications)")
                    await email_service.scan_inbox_for_replies(user_id)
                    scanned_count += 1
                    
                except Exception as e:
                    logger.error(f"Error scanning inbox for user {user.get('_id')}: {e}")
                    error_count += 1
                    continue
            
            logger.info(
                f"Email monitoring complete: {scanned_count} users scanned, "
                f"{error_count} errors"
            )
            
            return {
                "success": True,
                "scanned": scanned_count,
                "errors": error_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Critical error in scan_all_inboxes: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_scan())


@celery_app.task(name="app.workers.email_monitor.scan_user_inbox")
def scan_user_inbox(user_id: str):
    """
    Scan a specific user's inbox
    Can be triggered on-demand or scheduled per-user
    """
    async def _scan():
        try:
            db = await get_database()
            email_service = EmailIntelligenceService(db)
            
            # Verify user has Gmail connected
            user = await db.users.find_one(
                {"_id": user_id},
                {"gmail_auth": 1}
            )
            
            if not user or not user.get("gmail_auth"):
                logger.warning(f"User {user_id} has no Gmail connected")
                return {"success": False, "error": "No Gmail connected"}
            
            # Scan inbox
            logger.info(f"Scanning inbox for user {user_id}")
            await email_service.scan_inbox_for_replies(user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scanning inbox for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_scan())


@celery_app.task(name="app.workers.email_monitor.scan_recent_applications")
def scan_recent_applications():
    """
    Scan only applications from the last 7 days (more frequent monitoring)
    Runs every 15 minutes for recent applications
    """
    async def _scan():
        try:
            db = await get_database()
            email_service = EmailIntelligenceService(db)
            
            # Get applications from last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            recent_apps = await db.applications.find(
                {
                    "created_at": {"$gte": seven_days_ago},
                    "email_thread_id": {"$exists": True, "$ne": None},
                    "status": {
                        "$nin": [
                            "rejected",
                            "offer_accepted",
                            "withdrawn",
                            "archived"
                        ]
                    }
                },
                {"user_id": 1}
            ).to_list(length=None)
            
            if not recent_apps:
                logger.info("No recent applications to monitor")
                return {"success": True, "scanned": 0}
            
            # Get unique user IDs
            user_ids = list(set(str(app["user_id"]) for app in recent_apps))
            
            scanned_count = 0
            for user_id in user_ids:
                try:
                    await email_service.scan_inbox_for_replies(user_id)
                    scanned_count += 1
                except Exception as e:
                    logger.error(f"Error scanning for user {user_id}: {e}")
                    continue
            
            logger.info(f"Scanned {scanned_count} users with recent applications")
            
            return {
                "success": True,
                "scanned": scanned_count,
                "applications_checked": len(recent_apps),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in scan_recent_applications: {e}")
            return {"success": False, "error": str(e)}
    
    return run_async(_scan())
