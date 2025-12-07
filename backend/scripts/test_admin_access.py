
import sys
import os
import asyncio
from httpx import AsyncClient

# Add parent directory to path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.config import settings
    from app.core.security import create_access_token
    from app.database import init_database, db
    from pymongo import MongoClient
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test_access():
    print("1. Connecting to DB...")
    # Initialize DB (needed for finding user ID if we want to be precise, though create_access_token only needs an ID)
    client = MongoClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    user = database.users.find_one({"email": "cjmatheka@gmail.com"})
    
    if not user:
        print("ERROR: User cjmatheka@gmail.com not found in DB.")
        return
        
    print(f"   found user: {user['_id']} (Role: {user.get('role')})")
    
    print("2. Generating Token...")
    # Generate token locally exactly as the auth endpoint would
    access_token = create_access_token(subject=str(user["_id"]))
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("3. Testing Admin Endpoint (GET /api/v1/admin/stats)...")
    async with AsyncClient(app=None, base_url="http://localhost:8000") as ac:
        try:
            # We are hitting the running server from within the container
            response = await ac.get("/api/v1/admin/stats", headers=headers)
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("\nSUCCESS: The backend recognizes this user as Admin.")
            else:
                print(f"\nFAILURE: The backend returned {response.status_code}.")
                
        except Exception as e:
            print(f"   Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_access())
