import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import hash_password, generate_referral_code
from datetime import datetime

async def create_admin():
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Use 'mongo' hostname for Docker environment
    client = AsyncIOMotorClient("mongodb://mongo:27017")
    db = client.vision_ai
    
    # Check if admin exists
    existing = await db.users.find_one({"email": "admin@cvision.com"})
    if existing:
        print("Admin user already exists")
        # Update to ensure it has admin role
        await db.users.update_one(
            {"email": "admin@cvision.com"},
            {"$set": {"role": "admin", "password": hash_password("admin123")}}
        )
        print("Updated existing user to admin with new password")
        client.close()
        return
    
    admin_user = {
        "email": "admin@cvision.com",
        "password": hash_password("admin123"),
        "first_name": "Admin",
        "last_name": "User",
        "phone": None,
        "role": "admin",
        "is_active": True,
        "is_verified": True,
        "subscription_tier": "premium",
        "profile": None,
        "usage_stats": {
            "total_searches": 0,
            "total_applications": 0,
            "successful_applications": 0,
            "cv_customizations": 0,
            "cover_letters_generated": 0,
            "monthly_searches": 0,
            "daily_searches": 0,
            "success_rate": 0.0,
            "avg_applications_per_search": 0.0
        },
        "preferences": {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
            "marketing_emails": False,
            "application_reminders": True,
            "job_alerts": True,
            "weekly_reports": True,
            "language": "en",
            "theme": "light",
            "dashboard_layout": "default"
        },
        "referral_code": generate_referral_code(),
        "referred_by": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": None,
        "verified_at": datetime.utcnow(),
        "cv_uploaded_at": None,
        "terms_accepted": True,
        "newsletter_subscription": False
    }
    
    result = await db.users.insert_one(admin_user)
    print(f"Admin created with ID: {result.inserted_id}")
    print("Email: admin@cvision.com")
    print("Password: admin123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin())