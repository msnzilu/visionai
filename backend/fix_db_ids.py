import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "vision_ai"

async def fix_application_ids():
    print(f"Connecting to {MONGO_URL}...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("Checking for applications with ObjectId user_id or job_id...")
    
    # Find applications where user_id is an ObjectId
    cursor = db.applications.find({})
    
    count = 0
    fixed = 0
    
    async for app in cursor:
        count += 1
        needs_update = False
        update_data = {}
        
        # Check user_id
        if isinstance(app.get("user_id"), ObjectId):
            print(f"Fixing user_id for app {app['_id']}")
            update_data["user_id"] = str(app["user_id"])
            needs_update = True
            
        # Check job_id
        if isinstance(app.get("job_id"), ObjectId):
            print(f"Fixing job_id for app {app['_id']}")
            update_data["job_id"] = str(app["job_id"])
            needs_update = True
            
        if needs_update:
            await db.applications.update_one(
                {"_id": app["_id"]},
                {"$set": update_data}
            )
            fixed += 1
            
    print(f"Scanned {count} applications.")
    print(f"Fixed {fixed} applications.")

if __name__ == "__main__":
    asyncio.run(fix_application_ids())
