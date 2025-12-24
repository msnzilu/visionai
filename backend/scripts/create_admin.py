import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from datetime import datetime
from urllib.parse import quote_plus

# Connection Settings
# URL-encode the username and password to handle special characters
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")

MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DB_NAME = "synovae_db"

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
        print("Password: password123")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_admin())