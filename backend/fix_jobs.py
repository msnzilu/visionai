import asyncio
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def fix_jobs():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    print("--- Fixing Job Data for Testing ---")
    
    # Update last 10 jobs to be active and have an email
    recent_jobs = await db.jobs.find().sort("created_at", -1).limit(10).to_list(length=10)
    
    count = 0
    for job in recent_jobs:
        await db.jobs.update_one(
            {"_id": job["_id"]},
            {
                "$set": {
                    "is_active": True,
                    "email": "test_recruiter@example.com", # Dummy email for testing
                    "updated_at": datetime.utcnow(),
                    "created_at": datetime.utcnow() # Make them brand new to pass 7-day filter
                }
            }
        )
        count += 1
        
    print(f"Updated {count} jobs with is_active=True and dummy email.")

if __name__ == "__main__":
    asyncio.run(fix_jobs())
