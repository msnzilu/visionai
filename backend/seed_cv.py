
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# DB Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017") 
DB_NAME = os.getenv("MONGO_DB_NAME", "vision_ai")

async def seed_cv():
    print(f"Connecting to {MONGO_URI} (DB: {DB_NAME})...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Check count
    count = await db.users.count_documents({})
    print(f"Found {count} users in database.")
    
    if count == 0:
        print("CRITICAL: No users found to update!")
        return

    # Mock CV Data
    mock_cv = {
        "summary": "Experienced Full Stack Developer with a focus on Python and JavaScript ecosystems.",
        "skills": ["Python", "JavaScript", "React", "Node.js", "MongoDB", "Docker", "AWS", "FastAPI"],
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Solutions",
                "start_date": "2020-01",
                "end_date": "Present",
                "description": "Leading development of cloud-native applications."
            }
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "school": "University of Technology",
                "year": "2017"
            }
        ],
        "contact_info": {
            "email": "jcharlesmila8@gmail.com",
            "phone": "+1234567890",
            "location": "Remote"
        }
    }

    # Update ALL users
    print("Injecting mock CV data into all users...")
    
    result = await db.users.update_many(
        {}, 
        {"$set": {"cv_data": mock_cv}}
    )
    
    print(f"Matched {result.matched_count} users, Modified {result.modified_count} users.")
    
    # Verify immediately
    users = await db.users.find({}).to_list(length=10)
    for u in users:
        print(f"User {u['_id']} keys: {list(u.keys())}")
        if "cv_data" in u:
            print(f"  -> SUCCESS: cv_data found for {u['email']}")
        else:
            print(f"  -> FAIL: cv_data MISSING for {u['email']}")

if __name__ == "__main__":
    asyncio.run(seed_cv())
