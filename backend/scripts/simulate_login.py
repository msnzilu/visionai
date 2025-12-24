"""
Test admin login by simulating the exact login flow
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
import bcrypt
from datetime import datetime

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

async def simulate_login():
    """Simulate the exact login flow from auth.py"""
    
    admin_email = "admin@synovae.io"
    test_password = "Admin@2024!"
    
    print("=" * 60)
    print("Simulating Admin Login Flow")
    print("=" * 60)
    
    try:
        # Connect
        print(f"\n🔌 Connecting...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        await client.admin.command('ping')
        db = client[DATABASE_NAME]
        
        # Find user (line 208 in auth.py)
        print(f"\n🔍 Finding user: {admin_email}")
        user = await db.users.find_one({"email": admin_email})
        
        if not user:
            print("❌ User not found!")
            return
        
        print(f"✅ User found")
        
        # Verify password (line 209)
        print(f"\n🔐 Verifying password...")
        if not verify_password(test_password, user["password"]):
            print("❌ Password verification failed!")
            return
        
        print(f"✅ Password verified")
        
        # Check is_verified (line 215-220)
        print(f"\n✅ Checking verification status...")
        is_verified = user.get("is_verified", False)
        print(f"   is_verified: {is_verified}")
        
        if not is_verified:
            print("❌ Email not verified!")
            return
        
        print(f"✅ User is verified")
        
        # Create full_name (line 267-270)
        print(f"\n👤 Creating user response...")
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        if not full_name:
            full_name = user["email"].split("@")[0]
        print(f"   full_name: {full_name}")
        
        # THIS IS THE CRITICAL LINE THAT MIGHT FAIL (line 276)
        print(f"\n📅 Processing created_at field...")
        created_at = user.get("created_at")
        print(f"   created_at type: {type(created_at)}")
        print(f"   created_at value: {created_at}")
        
        if created_at:
            try:
                created_at_iso = created_at.isoformat()
                print(f"   created_at ISO: {created_at_iso}")
            except Exception as e:
                print(f"   ❌ ERROR converting to ISO: {e}")
                print(f"   This is likely the login error!")
        else:
            print(f"   ⚠️  created_at is None/missing!")
        
        # Build user response
        user_response = {
            "id": str(user["_id"]),
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "full_name": full_name,
            "role": user.get("role", "user"),
            "subscription_tier": user["subscription_tier"],
            "created_at": created_at.isoformat() if created_at else datetime.utcnow().isoformat(),
            "gmail_connected": bool(user.get("gmail_auth"))
        }
        
        print("\n" + "=" * 60)
        print("✅ LOGIN SIMULATION SUCCESSFUL!")
        print("=" * 60)
        print(f"\nUser Response:")
        for key, value in user_response.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"\n❌ ERROR DURING LOGIN: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  This is the error you're seeing during login!")
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(simulate_login())
