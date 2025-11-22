#!/usr/bin/env python3
"""Drop indexes and seed database"""

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

async def reset_and_seed():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.job_platform
    
    # Drop all indexes except _id
    try:
        await db.jobs.drop_indexes()
        print("✅ Dropped all indexes")
    except Exception as e:
        print(f"⚠️  Could not drop indexes: {e}")
    
    # Delete all jobs
    result = await db.jobs.delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} jobs")
    
    # Insert one simple job to test
    job = {
        "title": "Test Job",
        "description": "This is a test job",
        "company_name": "Test Company",
        "location": "Remote",
        "status": "active",
        "source": "manual",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.jobs.insert_one(job)
    print(f"✅ Inserted test job with ID: {result.inserted_id}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_and_seed())
