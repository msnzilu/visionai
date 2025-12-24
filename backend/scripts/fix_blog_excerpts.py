"""
Add missing excerpt field to all blog posts in Atlas
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

def generate_excerpt(content, max_length=200):
    """Generate excerpt from content"""
    # Remove HTML tags
    import re
    text = re.sub(r'<[^>]+>', '', content)
    # Get first max_length characters
    if len(text) <= max_length:
        return text
    # Find last space before max_length
    excerpt = text[:max_length]
    last_space = excerpt.rfind(' ')
    if last_space > 0:
        excerpt = excerpt[:last_space]
    return excerpt + '...'

async def fix_blog_posts():
    """Add missing excerpt field to blog posts"""
    
    print("=" * 60)
    print("Adding Missing Excerpt Field to Blog Posts")
    print("=" * 60)
    
    try:
        # Connect
        print(f"\n🔌 Connecting to Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        await client.admin.command('ping')
        print("✅ Connected")
        
        db = client[DATABASE_NAME]
        
        # Find all blog posts without excerpt
        print(f"\n🔍 Finding blog posts without excerpt...")
        posts = await db.blog_posts.find({"excerpt": {"$exists": False}}).to_list(length=100)
        
        print(f"Found {len(posts)} posts without excerpt\n")
        
        if len(posts) == 0:
            print("✅ All posts already have excerpts!")
            return
        
        # Update each post
        updated_count = 0
        for post in posts:
            title = post.get('title', 'Untitled')
            content = post.get('content', '')
            
            # Generate excerpt from content
            excerpt = generate_excerpt(content)
            
            # Update post
            result = await db.blog_posts.update_one(
                {"_id": post["_id"]},
                {
                    "$set": {
                        "excerpt": excerpt,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"✅ Updated: {title}")
                print(f"   Excerpt: {excerpt[:80]}...")
            else:
                print(f"⚠️  Failed to update: {title}")
        
        print(f"\n{'='*60}")
        print(f"✅ Updated {updated_count} blog posts")
        print(f"{'='*60}")
        
        # Verify
        print(f"\n🔍 Verifying updates...")
        remaining = await db.blog_posts.count_documents({"excerpt": {"$exists": False}})
        print(f"Posts without excerpt: {remaining}")
        
        if remaining == 0:
            print("✅ All blog posts now have excerpts!")
        
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
    asyncio.run(fix_blog_posts())
