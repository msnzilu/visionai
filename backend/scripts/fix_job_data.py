# Script to fix database job documents
# This fixes invalid data formats in existing job records

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

async def fix_job_documents():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    db = client.visionai
    jobs_collection = db.jobs
    
    # Find all jobs
    cursor = jobs_collection.find({})
    jobs = await cursor.to_list(length=None)
    
    print(f"Found {len(jobs)} jobs to check")
    
    fixed_count = 0
    for job in jobs:
        needs_update = False
        updates = {}
        
        # Fix benefits if it's a list of strings
        if "benefits" in job and isinstance(job["benefits"], list):
            if job["benefits"] and isinstance(job["benefits"][0], str):
                needs_update = True
                updates["benefits"] = []
                print(f"Fixed benefits for job: {job.get('title', 'Unknown')}")
        
        # Fix requirements if it's a list of strings
        if "requirements" in job and isinstance(job["requirements"], list):
            if job["requirements"] and isinstance(job["requirements"][0], str):
                needs_update = True
                updates["requirements"] = []
                print(f"Fixed requirements for job: {job.get('title', 'Unknown')}")
        
        # Ensure required fields have defaults
        if "employment_type" not in job:
            updates["employment_type"] = None
            needs_update = True
        
        if "work_arrangement" not in job:
            updates["work_arrangement"] = None
            needs_update = True
        
        if "experience_level" not in job:
            updates["experience_level"] = None
            needs_update = True
        
        if "view_count" not in job:
            updates["view_count"] = 0
            needs_update = True
        
        if "application_count" not in job:
            updates["application_count"] = 0
            needs_update = True
        
        if needs_update:
            await jobs_collection.update_one(
                {"_id": job["_id"]},
                {"$set": updates}
            )
            fixed_count += 1
    
    print(f"Fixed {fixed_count} jobs")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_job_documents())
