import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys

# ATLAS URI with encoded password
MONGO_URI = "mongodb+srv://jcharles:HxHxHz%40%23%402030@synovae.wvyba4e.mongodb.net/?appName=synovae"
DB_NAME = "synovae_db"

async def init_db():
    print(f"Connecting to Atlas...")
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Insert a temporary document to force DB creation
        print("Inserting initialization document...")
        collection = db.init_check
        result = await collection.insert_one({"status": "db_created", "timestamp": datetime.now() if 'datetime' in globals() else "now"})
        
        print(f"Successfully inserted document with ID: {result.inserted_id}")
        print(f"Database '{DB_NAME}' should now exist!")
        
        # Optional: Clean up (delete the doc, but keep DB? Mongo might drop DB if empty... 
        # let's keep it for a moment or just insert a config doc)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(init_db())
