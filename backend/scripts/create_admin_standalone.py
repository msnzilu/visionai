"""
Standalone script to create admin user in MongoDB Atlas
Does not require environment variables - uses direct connection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from datetime import datetime
from urllib.parse import quote_plus
import bcrypt

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

async def create_admin():
    """Create or recreate admin user with fresh password"""
    
    # Admin credentials
    admin_email = "admin@synovae.io"
    admin_password = "Admin@2024!"  # New stronger password
    
    print("=" * 60)
    print("Creating Admin User")
    print("=" * 60)
    
    try:
        # Generate fresh bcrypt hash
        print(f"\n🔐 Generating password hash...")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
        print(f"✅ Password hash generated")
        
        # Connect to MongoDB
        print(f"\n🔌 Connecting to MongoDB Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected successfully!")
        
        # Get database and collection
        db = client[DATABASE_NAME]
        users_collection = db.users
        
        # Check if admin exists
        existing = await users_collection.find_one({"email": admin_email})
        
        if existing:
            print(f"\n⚠️  Admin user '{admin_email}' already exists!")
            print("🗑️  Deleting existing admin user...")
            await users_collection.delete_one({"email": admin_email})
            print("✅ Deleted successfully")
        
        # Create new admin user
        print(f"\n🔨 Creating new admin user...")
        
        new_admin = {
            "email": admin_email,
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
            "referral_code": "ADMIN2024"
        }
        
        result = await users_collection.insert_one(new_admin)
        
        print("\n" + "=" * 60)
        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📧 Email:    {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print("\n" + "=" * 60)
        print("⚠️  IMPORTANT: Save these credentials securely!")
        print("=" * 60)
        
        # Verify the user was created
        print(f"\n🔍 Verifying user creation...")
        verify = await users_collection.find_one({"email": admin_email})
        if verify:
            print(f"✅ User verified in database")
            print(f"   Role: {verify.get('role')}")
            print(f"   Tier: {verify.get('subscription_tier')}")
            print(f"   Verified: {verify.get('is_verified')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print("\n🔌 Connection closed")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_admin())
