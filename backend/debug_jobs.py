import asyncio
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

async def debug_jobs():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    print("--- Job Database Debug ---")
    
    total_jobs = await db.jobs.count_documents({})
    print(f"Total jobs in DB: {total_jobs}")
    
    active_jobs = await db.jobs.count_documents({"is_active": True})
    print(f"Active jobs: {active_jobs}")
    
    jobs_with_email = await db.jobs.count_documents({"email": {"$exists": True, "$ne": None}})
    print(f"Jobs with email: {jobs_with_email}")
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_jobs = await db.jobs.count_documents({"created_at": {"$gte": seven_days_ago}})
    print(f"Jobs created in last 7 days: {recent_jobs}")
    
    valid_candidates = await db.jobs.count_documents({
        "is_active": True,
        "created_at": {"$gte": seven_days_ago},
        "email": {"$exists": True, "$ne": None}
    })
    print(f"Valid candidates (Active + Email + Recent): {valid_candidates}")

    # Check date range of all jobs
    print("--- DETAILED ACTIVE JOBS ---")
    active_job_list = await db.jobs.find({"is_active": True}).limit(10).to_list(length=10)
    for job in active_job_list:
        print(f"ID: {job.get('_id')} | Created: {job.get('created_at')} ({type(job.get('created_at'))}) | Email: {job.get('email')}")

    if not active_job_list:
        print("NO ACTIVE JOBS FOUND!")

if __name__ == "__main__":
    asyncio.run(debug_jobs())
