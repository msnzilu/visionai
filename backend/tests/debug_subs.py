
import asyncio
import os
import sys
import logging

# Setup path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# MOCK SETTINGS
os.environ["MONGODB_URL"] = "mongodb://mongo:27017/job_platform"
os.environ["DATABASE_NAME"] = "job_platform"
os.environ["PAYSTACK_SECRET_KEY"] = "sk_test_mock"
os.environ["PAYSTACK_PUBLIC_KEY"] = "pk_test_mock"
os.environ["REDIS_URL"] = "redis://redis:6379/0"
os.environ["CELERY_BROKER_URL"] = "redis://redis:6379/0"
os.environ["CELERY_RESULT_BACKEND"] = "redis://redis:6379/0"
os.environ["WEBHOOK_SECRET"] = "secret"

# Force settings update
from app.core import config
config.settings.MONGODB_URL = "mongodb://mongo:27017/job_platform"

from app.database import get_database
from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionTier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_annual_plan():
    db = await get_database()
    service = SubscriptionService(db)
    
    # 1. Create a dummy user
    email = "debug_annual@test.com"
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        await db.users.delete_one({"_id": existing_user["_id"]})
        await db.subscriptions.delete_one({"user_id": existing_user["_id"]})
        
    user_doc = {
        "email": email,
        "subscription_tier": "free",
        "is_active": True
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    logger.info(f"Created user {user_id}")
    
    # 2. Upgrade to Annual Plan
    # Simulate payment success
    try:
        await service.create_subscription(user_id, "plan_premium_annual")
        logger.info("Created Annual Subscription")
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        return
    
    # Check what user tier is set to
    user = await db.users.find_one({"_id": result.inserted_id})
    logger.info(f"User Subscription Tier: {user.get('subscription_tier')}")
    
    # 3. Call get_user_subscription multiple times (triggers sync)
    sub = await service.get_user_subscription(user_id)
    if sub:
        logger.info(f"Retrieved Subscription Plan: {sub.plan_id}")
        logger.info(f"Retrieved Subscription Interval: {sub.billing_interval}")
        
        # Verify
        if sub.plan_id == "plan_premium_annual":
            logger.info("SUCCESS: Annual plan persisted")
        else:
            logger.error(f"FAILURE: Plan reverted to {sub.plan_id}")
    else:
        logger.error("FAILURE: No subscription returned")

if __name__ == "__main__":
    asyncio.run(debug_annual_plan())
