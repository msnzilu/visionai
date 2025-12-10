
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def inspect_db():
    print("DB_CHECK_START")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    saved_jobs = await db.saved_jobs.find({
        "$or": [
            {"generated_cv_path": {"$regex": "\\.htm$"}},
            {"generated_cv_path": {"$regex": "\\.html$"}}
        ]
    }).to_list(length=100)
    
    if saved_jobs:
        print(f"HTM_FOUND: {len(saved_jobs)}")
        for job in saved_jobs:
            print(f"ID: {job.get('job_id')} PATH: {job.get('generated_cv_path')}")
    else:
        print("HTM_FOUND: 0")

if __name__ == "__main__":
    asyncio.run(inspect_db())
