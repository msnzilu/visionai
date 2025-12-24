"""
Convert published_at strings to datetime objects in blog posts
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

async def fix_published_at():
    """Convert string published_at to datetime objects"""
    
    print("=" * 60)
    print("Fixing published_at Field Format")
    print("=" * 60)
    
    try:
        # Connect
        print(f"\n🔌 Connecting to Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        await client.admin.command('ping')
        print("✅ Connected")
        
        db = client[DATABASE_NAME]
        
        # Get all blog posts
        posts = await db.blog_posts.find().to_list(length=100)
        
        updated_count = 0
        
        for post in posts:
            published_at = post.get('published_at')
            
            # Check if it's a string
            if isinstance(published_at, str):
                title = post.get('title', 'Untitled')[:50]
                print(f"\n📝 Fixing: {title}")
                print(f"   Current: {published_at} (string)")
                
                try:
                    # Parse string to datetime
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    # Remove timezone info to store as naive datetime
                    dt_naive = dt.replace(tzinfo=None)
                    
                    # Update in database
                    result = await db.blog_posts.update_one(
                        {"_id": post["_id"]},
                        {"$set": {"published_at": dt_naive}}
                    )
                    
                    if result.modified_count > 0:
                        print(f"   ✅ Updated to: {dt_naive} (datetime)")
                        updated_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to parse: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ Updated {updated_count} blog posts")
        print(f"{'='*60}")
        
        # Verify
        print(f"\n🔍 Verifying all posts now have datetime objects...")
        all_posts = await db.blog_posts.find().to_list(length=100)
        
        string_count = 0
        datetime_count = 0
        
        for post in all_posts:
            published_at = post.get('published_at')
            if isinstance(published_at, str):
                string_count += 1
            elif isinstance(published_at, datetime):
                datetime_count += 1
        
        print(f"   Datetime objects: {datetime_count}")
        print(f"   Strings remaining: {string_count}")
        
        if string_count == 0:
            print("\n✅ All published_at fields are now datetime objects!")
        else:
            print(f"\n⚠️  {string_count} posts still have string published_at")
        
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
    asyncio.run(fix_published_at())
