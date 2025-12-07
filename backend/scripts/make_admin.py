
import sys
import os
import asyncio
from pymongo import MongoClient

# Add parent directory to path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.config import settings
except ImportError:
    print("Could not import app settings. Please run this script from the backend directory or ensure PYTHONPATH is set.")
    sys.exit(1)

def make_admin(email):
    print(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
    try:
        client = MongoClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        user = db.users.find_one({"email": email})
        
        if not user:
            print(f"User with email '{email}' not found.")
            return False
            
        print(f"Found user: {user.get('email')} (Current role: {user.get('role', 'user')})")
        
        if user.get('role') == 'admin':
            print("User is already an admin.")
            return True
            
        result = db.users.update_one(
            {"email": email},
            {"$set": {"role": "admin"}}
        )
        
        if result.modified_count > 0:
            print(f"Successfully promoted {email} to admin!")
            return True
        else:
            print("Failed to update user role.")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)
        
    email = sys.argv[1]
    make_admin(email)
