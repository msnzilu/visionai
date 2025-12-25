"""
Check blog posts in Atlas for missing required fields
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

async def check_missing_fields():
    print("=" * 60)
    print("Checking Missing Fields")
    print("=" * 60)
    
    try:
        # Connect
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        db = client[DATABASE_NAME]
        
        # Get all posts
        posts = await db.blog_posts.find().to_list(length=100)
        
        required_fields = ["title", "slug", "categories", "tags", "status", "views", "reading_time"]
        
        for i, post in enumerate(posts, 1):
            print(f"\nPost {i}: {post.get('title', 'NO TITLE')}")
            missing = []
            for field in required_fields:
                if field not in post:
                    missing.append(field)
            
            if missing:
                print(f"❌ MISSING FIELDS: {missing}")
            else:
                print(f"✅ All required fields present")
                
            # Check values
            if "views" in post:
                print(f"   views: {post['views']} (Type: {type(post['views'])})")
            if "reading_time" in post:
                print(f"   reading_time: {post['reading_time']} (Type: {type(post['reading_time'])})")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_missing_fields())
