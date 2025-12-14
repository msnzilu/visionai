
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import sys

# Connection Settings
MONGODB_URL = "mongodb://13.51.158.58:27017"
DATABASE_NAME = "job_platform"

async def main():
    print(f"Connecting to MongoDB at {MONGODB_URL}...")
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        print(f"Connected to Database: {DATABASE_NAME}")
        
        # 1. Find an Admin User to be the author
        users_coll = db["users"]
        admin_user = await users_coll.find_one({"role": "admin"})
        if not admin_user:
            # Fallback to any user
            admin_user = await users_coll.find_one({})
        
        if not admin_user:
            print("ERROR: No users found in database to assign as author!")
            return

        # Constsruct Author Object
        profile = admin_user.get('profile') or {}
        author_data = {
            "user_id": str(admin_user["_id"]),
            "name": f"{admin_user.get('first_name', '')} {admin_user.get('last_name', '')}".strip() or admin_user.get('email', 'Admin'),
            "avatar_url": None,
            "bio": profile.get('bio')
        }
        
        print(f"Using Author: {author_data['name']} (ID: {author_data['user_id']})")
        
        
        # 2. Update Blog Posts
        blog_coll = db["blog_posts"]
        # Find posts where author DOES NOT exist OR author.user_id is None
        cursor = blog_coll.find({
            "$or": [
                {"author": {"$exists": False}},
                {"author.user_id": None}
            ]
        })
        
        updated_count = 0
        async for doc in cursor:
            print(f"Fixing Post: {doc.get('_id')} - {doc.get('title')}")
            
            result = await blog_coll.update_one(
                {"_id": doc["_id"]},
                {"$set": {"author": author_data}}
            )
            
            if result.modified_count > 0:
                print("  -> SUCCESS: Author added.")
                updated_count += 1
            else:
                print("  -> FAILED: Could not update.")
                
        print(f"\nTotal Posts Fixed: {updated_count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
