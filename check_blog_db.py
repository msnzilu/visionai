
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import json
import sys
from bson import ObjectId
from datetime import datetime

# Connection Settings
MONGODB_URL = "mongodb://13.51.158.58:27017"
DATABASE_NAME = "job_platform"

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

async def main():
    print(f"Connecting to MongoDB at {MONGODB_URL}...")
    try:
        with open("blog_dump.log", "w", encoding="utf-8") as f:
            client = AsyncIOMotorClient(MONGODB_URL)
            db = client[DATABASE_NAME]
            
            f.write(f"Connected to Database: {DATABASE_NAME}\n")
            
            collection_name = "blog_posts"
            coll = db[collection_name]
            count = await coll.count_documents({})
            f.write(f"\nCollection: {collection_name} (Total: {count})\n")
            
            if count > 0:
                f.write("\n--- Latest 5 Posts ---\n")
                # Sort by _id descending to get newest first
                cursor = coll.find({}).sort("_id", -1).limit(5)
                docs = []
                async for doc in cursor:
                    docs.append(doc)
                
                valid_author = None
                for doc in docs:
                    if "author" in doc:
                        valid_author = doc["author"]
                        break
                
                if valid_author:
                    f.write(f"\n--- Found Valid Author for Repair ---\n")
                    f.write(json.dumps(valid_author, indent=2))
                    f.write("\n-------------------------------------\n")

                for doc in docs:
                    if "author" not in doc:
                         f.write(f"\n!!! WARNING: Post {doc.get('_id')} is missing 'author' field !!!\n")
                    f.write(json.dumps(doc, cls=JSONEncoder, indent=2))
                    f.write("\n" + "-" * 50 + "\n")
                    
        print("Done. Check blog_dump.log")
                    
    except Exception as e:
        print(f"Error: {e}")
        with open("blog_dump.log", "a", encoding="utf-8") as f:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
