import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from datetime import datetime
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

# Use settings from environment
MONGODB_URL = settings.MONGODB_URL
DB_NAME = settings.DATABASE_NAME

async def create_admin():
    print(f"Connecting to {DB_NAME}...")
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        users_collection = db.users
        
        email = "admin@synovae.io"
        
        # Check if user exists
        existing = await users_collection.find_one({"email": email})
        if existing:
            print(f"User {email} already exists. Updating role to Admin...")
            await users_collection.update_one(
                {"email": email},
                {"$set": {
                    "role": "admin",
                    "is_superuser": True,
                    "is_verified": True,
                    "subscription_tier": "premium",
                    "subscription_status": "active"
                }}
            )
            print("User updated successfully.")
            return

        # Create new user
        print(f"Creating new admin user: {email}")
        
        # Hash for 'password123' (bcrypt)
        hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymVFt7H.8O.7d3x/j1a6."
        
        new_user = {
            "email": email,
            "password": hashed_password,
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "is_active": True,
            "is_superuser": True,
            "is_verified": True,
            "subscription_tier": "premium",
            "subscription_status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "usage_stats": {},
            "preferences": {},
            "profile": {},
            "referral_code": "ADMIN123"
        }
        
        await users_collection.insert_one(new_user)
        print("Admin user created successfully!")
        print(f"Email: {email}")
        print("Password: {password}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_admin())