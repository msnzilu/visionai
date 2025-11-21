"""Quick test to see if we can connect to MongoDB and insert a job"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from datetime import datetime

async def test_insert():
    print(f"Connecting to: {settings.MONGODB_URL}")
    print(f"Database: {settings.DATABASE_NAME}")
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    jobs_collection = db.jobs
    
    test_job = {
        "title": "Test Job",
        "company": "Test Company",
        "location": "Remote",
        "description": "Test description",
        "employment_type": "full_time",
        "experience_level": "mid",
        "salary_min": 100000,
        "salary_max": 150000,
        "currency": "USD",
        "industry": "technology",
        "required_skills": ["Python"],
        "preferred_skills": ["Docker"],
        "benefits": ["Remote work"],
        "remote_allowed": True,
        "visa_sponsorship": False,
        "application_url": "https://test.com/job",
        "source": "manual",
        "posted_date": datetime.utcnow(),
        "application_deadline": datetime.utcnow(),
        "is_active": True,
        "view_count": 0,
        "application_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {
            "scraped": False,
            "verified": True,
            "featured": False
        }
    }
    
    try:
        result = await jobs_collection.insert_one(test_job)
        print(f"✅ Successfully inserted job with ID: {result.inserted_id}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}")
        print(f"❌ Message: {str(e)}")
        import traceback
        traceback.print_exc()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_insert())
