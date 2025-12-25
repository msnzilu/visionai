"""
Check blog posts in Atlas to see their status and other relevant fields
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
from datetime import datetime

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

async def check_posts_status():
    """Check blog posts status"""
    
    print("=" * 60)
    print("Checking Blog Posts Status")
    print("=" * 60)
    
    try:
        # Connect
        print(f"\n🔌 Connecting to Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        db = client[DATABASE_NAME]
        
        # Get count
        count = await db.blog_posts.count_documents({})
        print(f"Total documents in blog_posts: {count}")
        
        # Get all posts
        # posts = await db.blog_posts.find().to_list(length=100) # Original line, replaced by cursor iteration
        
        if count > 0:
            print(f"\nPOSTS DETAILS ({count} found):")
            cursor = db.blog_posts.find() # Define cursor here
            async for post in cursor:
                print("-" * 40)
                for key, value in post.items():
                    print(f"{key}: {value}")
            print("-" * 40) # Add a closing separator
        else:
            print("No posts found.") # Changed from "No published posts found." to "No posts found." for accuracy
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client: # Ensure client exists before closing
            client.close()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_posts_status())
