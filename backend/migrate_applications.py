import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def migrate_applications():
    """Add deleted_at field to all applications missing it"""
    # Direct connection to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.vision_ai
    
    print("\n--- Migrating Applications ---")
    
    # Find applications without deleted_at field
    missing_deleted_at = await db.applications.count_documents({"deleted_at": {"$exists": False}})
    print(f"Applications missing 'deleted_at' field: {missing_deleted_at}")
    
    if missing_deleted_at > 0:
        # Add deleted_at: None to all applications missing it
        result = await db.applications.update_many(
            {"deleted_at": {"$exists": False}},
            {"$set": {
                "deleted_at": None,
                "updated_at": None  # Also add updated_at if missing
                
            }}
        )
        print(f"✅ Updated {result.modified_count} applications")
    
    # Also add other missing fields for consistency
    print("\n--- Adding other missing standard fields ---")
    
    # Add updated_at if missing
    missing_updated_at = await db.applications.count_documents({"updated_at": {"$exists": False}})
    if missing_updated_at > 0:
        result = await db.applications.update_many(
            {"updated_at": {"$exists": False}},
            {"$set": {"updated_at": None}}
        )
        print(f"✅ Added updated_at to {result.modified_count} applications")
    
    # Add empty arrays for missing list fields
    for field in ["documents", "communications", "interviews", "tasks"]:
        missing = await db.applications.count_documents({field: {"$exists": False}})
        if missing > 0:
            result = await db.applications.update_many(
                {field: {"$exists": False}},
                {"$set": {field: []}}
            )
            print(f"✅ Added {field} to {result.modified_count} applications")
    
    # Verify the fix
    print("\n--- Verification ---")
    total = await db.applications.count_documents({})
    with_deleted_at = await db.applications.count_documents({"deleted_at": {"$exists": True}})
    print(f"Total applications: {total}")
    print(f"Applications with deleted_at field: {with_deleted_at}")
    print(f"Migration complete! ✅")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_applications())
