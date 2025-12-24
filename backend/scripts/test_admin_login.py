"""
Test script to verify the admin password hash works correctly
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
import bcrypt

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

async def test_admin_login():
    """Test if admin password verification works"""
    
    admin_email = "admin@synovae.io"
    test_password = "Admin@2024!"
    
    print("=" * 60)
    print("Testing Admin Login")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        print(f"\n🔌 Connecting to Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        await client.admin.command('ping')
        print("✅ Connected")
        
        # Get user from database
        db = client[DATABASE_NAME]
        user = await db.users.find_one({"email": admin_email})
        
        if not user:
            print(f"\n❌ User '{admin_email}' not found in database!")
            return
        
        print(f"\n✅ User found in database")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
        print(f"   Is Active: {user.get('is_active')}")
        print(f"   Is Verified: {user.get('is_verified')}")
        
        # Get stored password hash
        stored_hash = user.get('password')
        print(f"\n🔐 Password hash (first 30 chars): {stored_hash[:30]}...")
        
        # Test password verification
        print(f"\n🧪 Testing password: '{test_password}'")
        
        # Method 1: bcrypt verification
        try:
            is_valid = bcrypt.checkpw(
                test_password.encode('utf-8'),
                stored_hash.encode('utf-8')
            )
            print(f"   bcrypt.checkpw result: {is_valid}")
            
            if is_valid:
                print("\n✅ PASSWORD VERIFICATION SUCCESSFUL!")
                print(f"   You can login with:")
                print(f"   Email: {admin_email}")
                print(f"   Password: {test_password}")
            else:
                print("\n❌ PASSWORD VERIFICATION FAILED!")
                print("   The stored hash doesn't match the password")
                
        except Exception as e:
            print(f"\n❌ Error during verification: {e}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_admin_login())
