import asyncio
import logging
from app.database import get_database, init_database
from app.workers.email_campaigns import process_daily_job_digest
from app.models.user import User
from bson import ObjectId
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_digest():
    """
    Test the daily job digest email with deduplication checks.
    """
    await init_database()
    db = await get_database()
    
    # Debug: Check job availability
    total_jobs = await db.jobs.count_documents({})
    # Check "active" jobs created recently
    recent_criteria = {"created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}, "is_active": True}
    recent_jobs = await db.jobs.count_documents(recent_criteria)
    
    logger.info(f"DB Stats: Total Jobs: {total_jobs}, Recent Active (7d): {recent_jobs}")

    # Seed mock jobs if needed
    if recent_jobs < 3:
        logger.info("Seeding mock jobs for testing...")
        mock_jobs = [
            {
                "title": f"Mock Job {i}",
                "company": "Test Corp",
                "location": "Remote",
                "description": "Test job description",
                "requirements": ["Python", "Test"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "type": "Full-time",
                "email": f"jobs{i}@test.com"
            } for i in range(5)
        ]
        await db.jobs.insert_many(mock_jobs)
        logger.info("Seeded 5 mock jobs.")

    # 1. Find a test user
    user = await db.users.find_one({"email": "jcharlesmail8@gmail.com"})
    if not user:
        user = await db.users.find_one({"cv_data": {"$exists": True}})
        
    if not user:
        logger.error("No suitable test user found with CV data.")
        return

    logger.info(f"Testing digest for user: {user.get('email')} ({user.get('_id')})")
    
    # Clear history for this user to ensure clean state
    # await db.email_history.delete_many({"user_id": str(user["_id"])})
    # logger.info("Cleared email history for user.")

    # --- RUN 1 (Should Send) ---
    logger.info("--- RUN 1 ---")
    result1 = await process_daily_job_digest()
    logger.info(f"Run 1 Result: {result1}")
    
    # --- RUN 2 (Should Skip - Frequency Check) ---
    logger.info("--- RUN 2 (Frequency Check) ---")
    result2 = await process_daily_job_digest()
    logger.info(f"Run 2 Result: {result2}")
    
    if result2.get("sent") == 0:
        logger.info("✅ Run 2 skipped as expected.")
    else:
        logger.warning(f"⚠️ Run 2 sent {result2.get('sent')} emails (Expected 0). Check logic.")

    # --- RUN 3 (Deduplication Check) ---
    logger.info("--- RUN 3 (Deduplication Check) ---")
    # Trick: Update last history to be yesterday so it passes frequency check
    # But keep the job_ids so they should be excluded
    last_entry = await db.email_history.find_one(
        {"user_id": str(user["_id"]), "type": "daily_digest"}, 
        sort=[("sent_at", -1)]
    )
    
    if last_entry:
        yesterday = datetime.utcnow() - timedelta(days=1, hours=1)
        await db.email_history.update_one(
            {"_id": last_entry["_id"]},
            {"$set": {"sent_at": yesterday}}
        )
        logger.info("Modified last history entry to appear as sent yesterday.")
        
        result3 = await process_daily_job_digest()
        logger.info(f"Run 3 Result: {result3}")
        # Note: If we only have 3 jobs and sent 3, result3 might be 0 sent because no matching jobs left.
        # That is also a valid deduplication result!
        
    logger.info("Test Complete.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_digest())
