import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus

# Connection details
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

BROKEN_PATHS = [
    "/assets/images/blog/default-hero.jpg",
    "/assets/images/blog/default-thumb.jpg",
    "assets/images/blog/default-hero.jpg",
    "assets/images/blog/default-thumb.jpg"
]

async def fix_images():
    print(f"Connecting to {DATABASE_NAME}...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("\nChecking for broken image paths...")
    query = {"featured_image": {"$in": BROKEN_PATHS}}
    count = await db.blog_posts.count_documents(query)
    print(f"Found {count} posts with broken image paths.")
    
    if count > 0:
        print("Nullifying broken paths...")
        result = await db.blog_posts.update_many(
            query,
            {"$set": {"featured_image": None}}
        )
        print(f"Updated {result.modified_count} posts.")
    
    # Also check if featured_image is an empty string or just whitespace
    query_empty = {"featured_image": {"$in": ["", " ", None]}}
    # (None is already handled by truthy check in JS, but cleaning up is good)
    
    # Let's see if any posts have OTHER image paths that might be broken
    print("\nRemaining image paths:")
    async for post in db.blog_posts.find({"featured_image": {"$ne": None}}):
        print(f" - {post.get('title')[:30]}: {post.get('featured_image')}")
        
    client.close()
    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(fix_images())
