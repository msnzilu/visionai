import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Adjust connection string as needed for your production environment
# If running inside docker, it might be 'mongodb://mongo:27017'
# If running locally to connect to remote, you might need an SSH tunnel or port forward
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "job_platform" # Confirmed from seed_jobs.py line 12

async def check_jobs():
    print(f"Connecting to {MONGO_URI}...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    collection = db.jobs
    
    total_count = await collection.count_documents({})
    active_count = await collection.count_documents({"status": "active"})
    missing_status_count = await collection.count_documents({"status": {"$exists": False}})
    
    print(f"Total Jobs: {total_count}")
    print(f"Active Jobs: {active_count}")
    print(f"Jobs with NO status: {missing_status_count}")
    
    if missing_status_count > 0:
        print("\nWARNING: You have jobs without a 'status' field.")
        print("The frontend ONLY shows jobs where status='active'.")
        
        # Show a sample
        sample = await collection.find_one({"status": {"$exists": False}})
        print(f"\nSample invalid job: {sample.get('title', 'Unknown Title')}")
        print(f"ID: {sample.get('_id')}")

if __name__ == "__main__":
    asyncio.run(check_jobs())
