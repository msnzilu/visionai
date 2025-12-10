
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import pprint

# Force correct DB URL if needed, or rely on settings
# settings.MONGODB_URL should be available if env is set or default
# Adjust if running locally without .env

async def main():
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    print(f"Database: {settings.DATABASE_NAME}")
    
    # helper to print
    async def count_and_print(collection_name):
        coll = db[collection_name]
        count = await coll.count_documents({})
        print(f"\nCollection: {collection_name} (Total: {count})")
        
        if count > 0:
            print("--- Sample Document ---")
            sample = await coll.find_one({})
            pprint.pprint(sample)
            
            # Check statuses
            print("\n--- Status Breakdown ---")
            pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
            async for doc in coll.aggregate(pipeline):
                print(f"Status '{doc['_id']}': {doc['count']}")

    await count_and_print("blog_posts")

if __name__ == "__main__":
    asyncio.run(main())
