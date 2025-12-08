import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Use environment variable for connection, default to localhost for local testing
# In Docker, this will pick up the MONGODB_URL from the environment if set, 
# or we can pass it manually.
# The backend container uses MONGODB_URL specific format.
MONGO_URI = os.getenv("MONGODB_URL", "mongodb://mongodb:27017/job_platform")
DB_NAME = "job_platform"

async def fix_jobs():
    print(f"Connecting to DB...")
    # Handle the case where MONGODB_URL might include the db name or not
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    collection = db.jobs
    
    # query for missing status
    query = {"status": {"$exists": False}}
    
    count = await collection.count_documents(query)
    print(f"Found {count} jobs with missing status.")
    
    if count > 0:
        print("Fixing jobs...")
        result = await collection.update_many(
            query,
            {"$set": {"status": "active"}}
        )
        print(f"✅ Successfully updated {result.modified_count} jobs to status='active'.")
    else:
        print("No jobs needed fixing.")

if __name__ == "__main__":
    asyncio.run(fix_jobs())
