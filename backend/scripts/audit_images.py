import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

async def audit_images():
    print("Connecting to Atlas...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    print("\nAuditing Blog Post Images:")
    async for post in db.blog_posts.find():
        title = post.get('title', 'Untitled')
        image = post.get('featured_image')
        status = post.get('status')
        print(f"Title: {title[:30]} | Image: {image} | Status: {status}")
    
    client.close()
    print("\nDone.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(audit_images())
