import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def debug_applications():
    # Direct connection to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.vision_ai
    
    print("\n--- Inspecting Applications Collection ---")
    count = await db.applications.count_documents({})
    print(f"Total applications in DB: {count}")
    
    print("\n--- Latest 5 Applications ---")
    cursor = db.applications.find({}).sort("created_at", -1).limit(5)
    async for app in cursor:
        print(f"ID: {app.get('_id')}")
        print(f"User ID: {app.get('user_id')} (Type: {type(app.get('user_id')).__name__})")
        print(f"Job Title: {app.get('job_title')}")
        print(f"Status: {app.get('status')}")
        print(f"Source: {app.get('source')}")
        print(f"Deleted At: {app.get('deleted_at')}")
        print(f"Created At: {app.get('created_at')}")
        print("-" * 50)

    print("\n--- Checking Filter Criteria ---")
    # Simulate the query used by the API
    latest = await db.applications.find_one({}, sort=[("created_at", -1)])
    if latest:
        user_id = latest.get("user_id")
        print(f"Testing Query for User ID: {user_id}")
        query = {"user_id": user_id, "deleted_at": None}
        count_filtered = await db.applications.count_documents(query)
        print(f"Matches for {{'user_id': '{user_id}', 'deleted_at': None}}: {count_filtered}")
        
        # Check if deleted_at field exists
        has_deleted_at = await db.applications.count_documents({"deleted_at": {"$exists": True}})
        print(f"Documents with 'deleted_at' field: {has_deleted_at}")
        
        # Check if deleted_at is missing (not None, but missing)
        missing_deleted_at = await db.applications.count_documents({"deleted_at": {"$exists": False}})
        print(f"Documents WITHOUT 'deleted_at' field: {missing_deleted_at}")
        
        if count_filtered == 0:
            print("\n!!! QUERY MISMATCH DETECTED !!!")
            # Try debugging why
            q1 = {"user_id": user_id}
            c1 = await db.applications.count_documents(q1)
            print(f"Matches for user_id only: {c1}")
            
            q2 = {"deleted_at": None}
            c2 = await db.applications.count_documents(q2)
            print(f"Matches for deleted_at: None: {c2}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(debug_applications())
