import asyncio
import os
from app.database import get_database
from dotenv import load_dotenv

load_dotenv()

async def check_jobs():
    db = await get_database()
    count = await db.jobs.count_documents({})
    print(f'Total jobs: {count}')
    jobs = await db.jobs.find().limit(5).to_list(5)
    for job in jobs:
        print(f"Title: {job.get('title')}, Location: {job.get('location')}")

if __name__ == "__main__":
    asyncio.run(check_jobs())
