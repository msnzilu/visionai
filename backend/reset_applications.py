import asyncio
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

async def reset_apps():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    print("--- Resetting Applications for Testing ---")
    
    # Count before
    count = await db.applications.count_documents({})
    print(f"Total applications before reset: {count}")
    
    # Delete ALL applications (Hard Reset for testing)
    result = await db.applications.delete_many({})
    
    # Verify
    new_count = await db.applications.count_documents({})
    print(f"Deleted {result.deleted_count} applications. Remaining: {new_count}")

    # Also double check job status
    active_jobs = await db.jobs.count_documents({"is_active": True, "email": {"$exists": True}})
    print(f"Active jobs ready to be scanned: {active_jobs}")

if __name__ == "__main__":
    asyncio.run(reset_apps())
