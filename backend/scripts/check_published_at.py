"""
Check published_at field format in blog posts
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

async def check_published_at():
    """Check published_at field format"""
    
    print("=" * 60)
    print("Checking published_at Field Format")
    print("=" * 60)
    
    try:
        # Connect
        print(f"\n🔌 Connecting to Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        await client.admin.command('ping')
        print("✅ Connected")
        
        db = client[DATABASE_NAME]
        
        # Get all blog posts
        posts = await db.blog_posts.find().to_list(length=10)
        
        print(f"\nFound {len(posts)} blog posts\n")
        
        for post in posts:
            title = post.get('title', 'Untitled')[:50]
            published_at = post.get('published_at')
            
            print(f"\n📝 {title}")
            print(f"   published_at value: {published_at}")
            print(f"   published_at type: {type(published_at)}")
            
            # Check if it's a datetime object
            if isinstance(published_at, datetime):
                print(f"   ✅ Is datetime object")
                print(f"   ISO format: {published_at.isoformat()}")
            elif isinstance(published_at, str):
                print(f"   ⚠️  Is string (should be datetime)")
                # Try to parse it
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    print(f"   Can be parsed to: {dt}")
                except:
                    print(f"   ❌ Cannot parse as datetime")
            else:
                print(f"   ❌ Unexpected type!")
        
        # Check for missing published_at
        missing = await db.blog_posts.count_documents({"published_at": {"$exists": False}})
        print(f"\n📊 Posts without published_at: {missing}")
        
        # Check for null published_at
        null_count = await db.blog_posts.count_documents({"published_at": None})
        print(f"📊 Posts with null published_at: {null_count}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_published_at())
