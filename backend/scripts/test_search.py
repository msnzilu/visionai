
import asyncio
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.services.job_service import JobService
from app.models.job import JobFilter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search():
    print("🔍 Testing Job Search...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    job_service = JobService(db)
    
    # Test 1: Count total jobs in DB
    total_count = await db.jobs.count_documents({})
    print(f"📊 Total jobs in DB: {total_count}")
    
    # Test 2: Count active jobs
    active_count = await db.jobs.count_documents({"status": "active"})
    print(f"📊 Active jobs in DB: {active_count}")
    
    # Test 3: Run search_jobs with empty query (what frontend does)
    print("\n🧪 Running search_jobs(query=None)...")
    try:
        result = await job_service.search_jobs(
            query=None,
            location=None,
            filters=JobFilter(),
            page=1,
            size=20
        )
        
        jobs = result.get("jobs", [])
        total = result.get("total", 0)
        
        print(f"✅ Search returned {len(jobs)} jobs")
        print(f"✅ Total found: {total}")
        
        if len(jobs) > 0:
            print("\nFirst job sample:")
            print(f"Title: {jobs[0].title}")
            print(f"Company: {jobs[0].company_name}")
            print(f"Status: {jobs[0].status}")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        
    client.close()

if __name__ == "__main__":
    asyncio.run(test_search())
