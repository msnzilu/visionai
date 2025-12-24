"""Fix test job dates to be within last 7 days"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random

async def fix_dates():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["visionai"]
    
    now = datetime.utcnow()
    
    # Update all test jobs to have recent dates (0-2 days ago)
    result = await db.jobs.update_many(
        {"external_id": {"$regex": "^test_job_"}},
        {"$set": {
            "created_at": now - timedelta(days=1),
            "posted_date": now - timedelta(days=1)
        }}
    )
    print(f"Updated {result.modified_count} jobs with recent dates")
    
    # Verify job titles
    jobs = await db.jobs.find({"external_id": {"$regex": "^test_job_"}}).to_list(10)
    print("\nTest job titles:")
    for j in jobs:
        print(f"  - {j['title']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_dates())
