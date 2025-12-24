"""
Script to connect to MongoDB Atlas and check database/collection data
Uses direct connection without requiring all environment variables
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from urllib.parse import quote_plus

# Direct Atlas connection
username = quote_plus("jcharles")
password = quote_plus("HxHxHz@#@2030")
MONGODB_URL = f"mongodb+srv://{username}:{password}@synovae.wvyba4e.mongodb.net/?appName=synovae"
DATABASE_NAME = "synovae_db"

async def check_atlas_database():
    """Connect to Atlas and check database contents"""
    print("=" * 60)
    print("MongoDB Atlas Database Check")
    print("=" * 60)
    
    print(f"\n📊 Configuration:")
    print(f"   Database Name: {DATABASE_NAME}")
    print(f"   Cluster: synovae.wvyba4e.mongodb.net")
    
    try:
        # Connect to MongoDB
        print(f"\n🔌 Connecting to MongoDB Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Get database
        db = client[DATABASE_NAME]
        
        # List all collections
        print(f"\n📁 Collections in '{DATABASE_NAME}':")
        collections = await db.list_collection_names()
        
        if not collections:
            print("   ⚠️  No collections found")
        else:
            for collection_name in sorted(collections):
                count = await db[collection_name].count_documents({})
                print(f"   • {collection_name}: {count} documents")
        
        # Check users collection specifically
        if 'users' in collections:
            print(f"\n👥 Users Collection Details:")
            users_count = await db.users.count_documents({})
            print(f"   Total users: {users_count}")
            
            # Count by role
            admin_count = await db.users.count_documents({"role": "admin"})
            print(f"   Admin users: {admin_count}")
            
            # Count by subscription tier
            for tier in ["free", "basic", "premium"]:
                tier_count = await db.users.count_documents({"subscription_tier": tier})
                print(f"   {tier.capitalize()} tier: {tier_count}")
            
            # Show sample admin user (without password)
            admin_user = await db.users.find_one(
                {"role": "admin"},
                {"email": 1, "first_name": 1, "last_name": 1, "subscription_tier": 1, "created_at": 1, "_id": 0}
            )
            if admin_user:
                print(f"\n   Sample admin user:")
                for key, value in admin_user.items():
                    print(f"      {key}: {value}")
        
        # Check applications collection
        if 'applications' in collections:
            print(f"\n📝 Applications Collection:")
            apps_count = await db.applications.count_documents({})
            print(f"   Total applications: {apps_count}")
            
            # Count by status
            for status in ["pending", "submitted", "accepted", "rejected"]:
                status_count = await db.applications.count_documents({"status": status})
                if status_count > 0:
                    print(f"   {status.capitalize()}: {status_count}")
        
        # Check jobs collection
        if 'jobs' in collections:
            print(f"\n💼 Jobs Collection:")
            jobs_count = await db.jobs.count_documents({})
            print(f"   Total jobs: {jobs_count}")
            
            # Count active jobs
            active_jobs = await db.jobs.count_documents({"status": "active"})
            print(f"   Active jobs: {active_jobs}")
        
        # Check subscriptions
        if 'subscriptions' in collections:
            print(f"\n💳 Subscriptions Collection:")
            subs_count = await db.subscriptions.count_documents({})
            print(f"   Total subscriptions: {subs_count}")
            
            # Count by status
            for status in ["active", "canceled", "past_due"]:
                status_count = await db.subscriptions.count_documents({"status": status})
                if status_count > 0:
                    print(f"   {status.capitalize()}: {status_count}")
        
        print("\n" + "=" * 60)
        print("✅ Database check complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_atlas_database())
