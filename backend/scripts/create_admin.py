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
        
        email = "how to deleye and create admin agan by comnnecting to a;as with ,pngposh"
        password = "password123"  # Plain text password for display
        
        # Hash for 'password123' (bcrypt)
        hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymVFt7H.8O.7d3x/j1a6."
        
        # Check if user exists
        existing = await users_collection.find_one({"email": email})
        if existing:
            print(f"\n⚠️  User {email} already exists!")
            print("Deleting existing user and creating fresh...")
            await users_collection.delete_one({"email": email})
            print("✅ Existing user deleted.")

        # Create new user
        print(f"\n🔨 Creating new admin user: {email}")
        
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
        
        print("\n" + "=" * 60)
        print("✅ Admin user created successfully!")
        print("=" * 60)
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print("=" * 60)
        print("\n⚠️  IMPORTANT: Change this password after first login!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_admin())