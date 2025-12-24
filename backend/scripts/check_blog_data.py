"""
Check blog posts in Atlas to see what fields are present
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
import json

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

async def check_blog_posts():
    """Check blog posts structure"""
    
    print("=" * 60)
    print("Checking Blog Posts Data Structure")
    print("=" * 60)
    
    try:
        # Connect
        print(f"\n🔌 Connecting to Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        await client.admin.command('ping')
        print("✅ Connected")
        
        db = client[DATABASE_NAME]
        
        # Get blog posts
        print(f"\n📝 Fetching blog posts...")
        posts = await db.blog_posts.find().limit(3).to_list(length=3)
        
        print(f"Found {len(posts)} blog posts\n")
        
        for i, post in enumerate(posts, 1):
            print(f"\n{'='*60}")
            print(f"Post {i}: {post.get('title', 'No title')}")
            print(f"{'='*60}")
            
            # Remove _id for cleaner display
            post_copy = {k: v for k, v in post.items() if k != '_id'}
            
            print("\nFields present:")
            for key in sorted(post_copy.keys()):
                value = post_copy[key]
                if isinstance(value, str) and len(value) > 100:
                    print(f"  • {key}: {value[:100]}...")
                else:
                    print(f"  • {key}: {value}")
        
        # Check what fields blog.js expects
        print(f"\n{'='*60}")
        print("Fields blog.js expects:")
        print(f"{'='*60}")
        expected_fields = [
            "title",
            "slug",
            "excerpt",
            "featured_image",
            "published_at",
            "reading_time",
            "author.name",  # Nested
            "categories",  # Array
            "tags",  # Array
            "views"
        ]
        
        if posts:
            sample_post = posts[0]
            print("\nField check:")
            for field in expected_fields:
                if '.' in field:
                    # Nested field
                    parts = field.split('.')
                    value = sample_post.get(parts[0], {})
                    if isinstance(value, dict):
                        value = value.get(parts[1])
                    status = "✅" if value else "❌ MISSING"
                else:
                    value = sample_post.get(field)
                    status = "✅" if value is not None else "❌ MISSING"
                
                print(f"  {status} {field}")
        
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
    asyncio.run(check_blog_posts())
