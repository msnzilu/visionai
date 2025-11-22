#!/usr/bin/env python3
"""Clean all jobs from database"""

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def clean_jobs():
    client = AsyncIOMotorClient('mongodb://mongodb:27017')
    db = client.visionai
    
    result = await db.jobs.delete_many({})
    print(f'✅ Deleted {result.deleted_count} jobs from database')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_jobs())
