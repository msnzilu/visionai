
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# Get Mongo URI from env or use default
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "visionai"

async def check_db():
    print(f"Connecting to {MONGO_URI}...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Total Jobs
    total_jobs = await db.jobs.count_documents({})
    print(f"Total Jobs: {total_jobs}")
    
    # 2. Jobs with Email
    email_jobs = await db.jobs.count_documents({"email": {"$exists": True, "$ne": None}})
    print(f"Jobs with Email: {email_jobs}")
    
    # 3. Recent Jobs (7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_jobs = await db.jobs.count_documents({"created_at": {"$gte": seven_days_ago}})
    print(f"Jobs created in last 7 days: {recent_jobs}")
    
    # 4. Recent AND Email
    recent_email_jobs = await db.jobs.count_documents({
        "created_at": {"$gte": seven_days_ago},
        "email": {"$exists": True, "$ne": None}
    })
    print(f"Recent Email Jobs: {recent_email_jobs}")
    
    # 5. Sample Titles
    print("\nSample Job Titles (Recent & Email):")
    cursor = db.jobs.find({
        "created_at": {"$gte": seven_days_ago},
        "email": {"$exists": True, "$ne": None}
    }).limit(10)
    
    async for job in cursor:
        print(f"- {job.get('title')} (Email: {job.get('email')})")

    # 6. Check Active Status
    active_count = await db.jobs.count_documents({"is_active": True})
    print(f"\nActive Jobs: {active_count}")

if __name__ == "__main__":
    asyncio.run(check_db())
