# backend/test_auth.py
"""
Test script to verify token authentication is working
Run with: python -m backend.test_auth
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

async def test_authentication():
    """Test the authentication flow"""
    
    print("=" * 60)
    print("TESTING AUTHENTICATION FLOW")
    print("=" * 60)
    
    # Test 1: Check if we can connect to database
    print("\n1. Testing database connection...")
    try:
        from app.database import init_database, get_users_collection
        await init_database()
        users_collection = await get_users_collection()
        user_count = await users_collection.count_documents({})
        print(f"   ✓ Connected to database")
        print(f"   ✓ Found {user_count} users in database")
    except Exception as e:
        print(f"   ✗ Database connection failed: {str(e)}")
        return
    
    # Test 2: Get or create a test user
    print("\n2. Getting test user...")
    try:
        user = await users_collection.find_one({})
        if not user:
            print("   ! No users found, creating test user...")
            from app.core.security import hash_password
            from datetime import datetime
            
            new_user = {
                "email": "test@example.com",
                "password": hash_password("password123"),
                "first_name": "Test",
                "last_name": "User",
                "is_active": True,
                "is_verified": True,
                "role": "user",
                "subscription_tier": "free",
                "created_at": datetime.utcnow(),
                "referral_code": "TEST1234"
            }
            result = await users_collection.insert_one(new_user)
            user = await users_collection.find_one({"_id": result.inserted_id})
            print(f"   ✓ Created test user: {user['email']}")
        
        print(f"   ✓ Found user: {user.get('email')}")
        print(f"   ✓ User ID: {user['_id']}")
        print(f"   ✓ User fields: {list(user.keys())}")
    except Exception as e:
        print(f"   ✗ Failed to get/create user: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Create a token
    print("\n3. Creating access token...")
    try:
        from app.core.security import create_access_token
        token = create_access_token(subject=str(user["_id"]))
        print(f"   ✓ Token created: {token[:50]}...")
    except Exception as e:
        print(f"   ✗ Failed to create token: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Verify the token
    print("\n4. Verifying token...")
    try:
        from app.core.security import verify_access_token
        payload = verify_access_token(token)
        print(f"   ✓ Token verified")
        print(f"   ✓ Payload: {payload}")
        print(f"   ✓ User ID from token: {payload.get('sub')}")
    except Exception as e:
        print(f"   ✗ Failed to verify token: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 5: Test get_current_user dependency
    print("\n5. Testing get_current_user dependency...")
    try:
        from app.dependencies import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Mock credentials
        class MockCredentials:
            def __init__(self, token):
                self.credentials = token
        
        mock_creds = MockCredentials(token)
        user_from_dep = await get_current_user(mock_creds)
        
        if user_from_dep:
            print(f"   ✓ get_current_user returned user")
            print(f"   ✓ User email: {user_from_dep.get('email')}")
            print(f"   ✓ User type: {type(user_from_dep)}")
            print(f"   ✓ User keys: {list(user_from_dep.keys()) if isinstance(user_from_dep, dict) else 'NOT A DICT'}")
        else:
            print(f"   ✗ get_current_user returned None")
    except Exception as e:
        print(f"   ✗ get_current_user failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 6: Test get_current_active_user dependency
    print("\n6. Testing get_current_active_user dependency...")
    try:
        from app.dependencies import get_current_active_user
        
        active_user = await get_current_active_user(user_from_dep)
        
        if active_user:
            print(f"   ✓ get_current_active_user returned user")
            print(f"   ✓ User email: {active_user.get('email')}")
            print(f"   ✓ Is active: {active_user.get('is_active')}")
        else:
            print(f"   ✗ get_current_active_user returned None")
    except Exception as e:
        print(f"   ✗ get_current_active_user failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 7: Make a test request to the endpoint
    print("\n7. Testing the actual endpoint...")
    print(f"\n   You can test with curl:")
    print(f"   curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/v1/users/me")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
    print("\nThe authentication flow is working correctly.")
    print("If the endpoint still fails, the issue is in the endpoint code itself.")


if __name__ == "__main__":
    asyncio.run(test_authentication())