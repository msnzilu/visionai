"""
Update test jobs to include application_email for auto-apply testing
Run with: python update_test_jobs.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "vision_ai")

async def update_jobs():
    """Add application_email to all test jobs"""
    
    print(f"🔄 Updating test jobs with application_email...")
    print(f"   URL: {MONGODB_URL}")
    print(f"   Database: {DATABASE_NAME}")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    jobs_collection = db.jobs
    
    # Check connection
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Update all jobs with a test application email
    result = await jobs_collection.update_many(
        {"external_id": {"$regex": "^test_job_"}},
        {"$set": {"application_email": "test-apply@synovae.io"}}
    )
    
    print(f"✅ Updated {result.modified_count} jobs with application_email")
    
    # Verify
    sample = await jobs_collection.find_one({"external_id": "test_job_1"})
    if sample:
        print(f"📧 Sample job email: {sample.get('application_email')}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(update_jobs())
