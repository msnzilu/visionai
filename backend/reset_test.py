
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# DB Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017") 
DB_NAME = os.getenv("MONGO_DB_NAME", "vision_ai")

async def reset_applications():
    print(f"Connecting to {MONGO_URI} (DB: {DB_NAME})...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. Get the main test user (assuming first user found or specific email)
    # Since we don't have the user ID from the chat context, we'll clear ALL auto_apply applications
    # or ask the user to provide their email.
    # For dev environment, clearing all 'auto_apply' applications is usually safe and effective.
    
    print("Clearing ALL applications marked as source='auto_apply'...")
    result = await db.applications.delete_many({"source": "auto_apply"})
    print(f"Deleted {result.deleted_count} auto-apply records.")
    
    print("Clearing ALL applications marked as auto_applied=True...")
    result2 = await db.applications.delete_many({"auto_applied": True})
    print(f"Deleted {result2.deleted_count} auto_applied records.")
    
    # Also verify jobs exist
    count = await db.jobs.count_documents({"status": "active"})
    print(f"Current Active Jobs: {count}")

    print("\nReset complete. You can run the test again.")

if __name__ == "__main__":
    asyncio.run(reset_applications())
