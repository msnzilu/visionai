"""
Reproduce ValueError for BlogPostResponse
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
from bson import ObjectId
from app.schemas.blog import BlogPostResponse

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"
POST_ID = "694c98152d1f48e042b805ec"

async def reproduce_error():
    print("=" * 60)
    print("Reproduce ValueError")
    print("=" * 60)
    
    try:
        # Connect
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print(f"Fetching post {POST_ID}...")
        post = await db.blog_posts.find_one({"_id": ObjectId(POST_ID)})
        
        if not post:
            print("❌ Post not found in DB!")
            return

        print("Post found. Attempting to create BlogPostResponse...")
        
        try:
            post["id"] = str(post["_id"])
            data = {k: v for k, v in post.items() if k != "_id"}
            
            # Print data keys vs schema fields
            print(f"Data keys: {list(data.keys())}")
            
            response = BlogPostResponse(**data)
            print("✅ BlogPostResponse created successfully!")
            print(response.json())
            
        except Exception as e:
            print(f"❌ SUCCESS! Reproduced Error: {type(e).__name__}: {e}")
            if hasattr(e, 'errors'):
                 print(f"   Details: {e.errors()}")

    except Exception as e:
        print(f"\n❌ Script Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    # Hack to make imports work from script directory
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reproduce_error())
