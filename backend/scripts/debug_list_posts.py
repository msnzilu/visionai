"""
Debug BlogService list_posts validation errors
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
from app.services.blog_service import BlogService
from app.models.blog import BlogStatus

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

async def debug_list_posts():
    print("=" * 60)
    print("Debug List Posts")
    print("=" * 60)
    
    try:
        # Connect
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        service = BlogService(db)
        
        print("\nCalling list_posts(status=BlogStatus.PUBLISHED)...")
        result = await service.list_posts(status=BlogStatus.PUBLISHED)
        
        print(f"\nTotal: {result.total}")
        print(f"Returned: {len(result.posts)}")
        
        if len(result.posts) == 0 and result.total > 0:
            print("\n⚠️ Posts exist but were skipped! Capturing validation error...")
            # Re-run logic manually to catch exception
            cursor = service.collection.find({"status": "published"})
            async for post in cursor:
                print(f"\nTesting Post: {post.get('title')}")
                try:
                    from app.schemas.blog import BlogPostSummary
                    post["id"] = str(post["_id"])
                    # Remove _id
                    data = {k: v for k, v in post.items() if k != "_id"}
                    summary = BlogPostSummary(**data)
                    print("✅ Valid!")
                except Exception as e:
                    print(f"❌ Validation Error: {e}")
                    if hasattr(e, 'errors'):
                        print(f"   Details: {e.errors()}")
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    # Hack to make imports work from script directory
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_list_posts())
