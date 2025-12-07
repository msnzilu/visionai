
import sys
import os
from pymongo import MongoClient

# Add parent directory to path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.config import settings
except ImportError:
    print("Could not import app settings.")
    sys.exit(1)

def list_users():
    print(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
    try:
        client = MongoClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        users = list(db.users.find({}, {"email": 1, "role": 1, "first_name": 1, "last_name": 1, "_id": 0}))
        
        print(f"\nFound {len(users)} users:")
        print("-" * 60)
        print(f"{'Email':<30} | {'Role':<10} | {'Name'}")
        print("-" * 60)
        
        for user in users:
            email = user.get('email', 'N/A')
            role = user.get('role', 'user')
            name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            print(f"{email:<30} | {role:<10} | {name}")
            
        print("-" * 60)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    list_users()
