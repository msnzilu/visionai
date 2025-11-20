# backend/app/services/subscription_service.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from bson import ObjectId


from app.models.subscription import (
    Subscription, SubscriptionCreate, SubscriptionUpdate,
    SubscriptionStatus, SubscriptionPlan, UsageEvent,
    Payment, PaymentStatus, Invoice, InvoiceStatus,
    Money, Referral, ReferralProgram, SubscriptionLimits,
    UsageLimit, LimitType
)
from app.models.user import SubscriptionTier
from app.models.common import Currency
from app.integrations.stripe_client import StripeClient
from app.config import settings

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.stripe_client = StripeClient()
        
        # Helper function to create usage limits
        def create_limit(name: str, max_value: int, period: str = "monthly", reset: bool = True) -> UsageLimit:
            return UsageLimit(
                name=name,
                limit_type=LimitType.COUNT,
                max_value=max_value,
                period=period,
                reset_on_billing=reset
            )
        
        # Subscription plans configuration with proper limits
        self.PLANS = {
            SubscriptionTier.FREE: SubscriptionPlan(
                id="plan_free",
                name="Free Plan",
                tier=SubscriptionTier.FREE,
                description="Get started with basic features",
                price=Money(amount=0, currency=Currency.USD),
                billing_interval="monthly",
                trial_period_days=0,
                limits=SubscriptionLimits(
                    monthly_job_searches=create_limit("monthly_job_searches", 10),
                    monthly_applications=create_limit("monthly_applications", 5),
                    monthly_cv_generations=create_limit("monthly_cv_generations", 1),
                    monthly_cover_letters=create_limit("monthly_cover_letters", 0),
                    concurrent_applications=create_limit("concurrent_applications", 1, "instant", False),
                    max_jobs_per_search=3,
                    api_rate_limit_per_minute=10,
                    storage_mb=10,
                    team_members=1,
                    advanced_analytics=False,
                    priority_support=False,
                    white_label=False,
                    custom_integrations=False,
                    bulk_operations=False,
                    export_formats=["pdf"],
                    ai_model_version="basic",
                    data_retention_days=7
                ),
                features=[
                    "10 job searches per month",
                    "Up to 3 jobs per search",
                    "Basic CV customization",
                    "Email support"
                ],
                is_active=True,
                sort_order=0
            ),
            SubscriptionTier.BASIC: SubscriptionPlan(
                id="plan_basic",
                name="Basic Plan",
                tier=SubscriptionTier.BASIC,
                description="Perfect for active job seekers",
                price=Money(amount=2000, currency=Currency.USD),
                billing_interval="monthly",
                trial_period_days=7,
                limits=SubscriptionLimits(
                    monthly_job_searches=create_limit("monthly_job_searches", 100),
                    monthly_applications=create_limit("monthly_applications", 50),
                    monthly_cv_generations=create_limit("monthly_cv_generations", 20),
                    monthly_cover_letters=create_limit("monthly_cover_letters", 20),
                    concurrent_applications=create_limit("concurrent_applications", 5, "instant", False),
                    max_jobs_per_search=10,
                    api_rate_limit_per_minute=30,
                    storage_mb=100,
                    team_members=1,
                    advanced_analytics=False,
                    priority_support=True,
                    white_label=False,
                    custom_integrations=False,
                    bulk_operations=True,
                    export_formats=["pdf", "docx"],
                    ai_model_version="standard",
                    data_retention_days=30
                ),
                features=[
                    "100 job searches per month",
                    "Up to 10 jobs per search",
                    "Premium CV templates",
                    "AI-powered cover letters",
                    "Priority support",
                    "Basic analytics"
                ],
                is_popular=True,
                is_active=True,
                sort_order=1,
                stripe_price_id=getattr(settings, 'STRIPE_BASIC_PRICE_ID', None)
            ),
            SubscriptionTier.PREMIUM: SubscriptionPlan(
                id="plan_premium",
                name="Premium Plan",
                tier=SubscriptionTier.PREMIUM,
                description="Full automation for serious professionals",
                price=Money(amount=4900, currency=Currency.USD),
                billing_interval="monthly",
                trial_period_days=14,
                limits=SubscriptionLimits(
                    monthly_job_searches=create_limit("monthly_job_searches", 9999),
                    monthly_applications=create_limit("monthly_applications", 9999),
                    monthly_cv_generations=create_limit("monthly_cv_generations", 9999),
                    monthly_cover_letters=create_limit("monthly_cover_letters", 9999),
                    concurrent_applications=create_limit("concurrent_applications", 20, "instant", False),
                    max_jobs_per_search=50,
                    api_rate_limit_per_minute=100,
                    storage_mb=1000,
                    team_members=3,
                    advanced_analytics=True,
                    priority_support=True,
                    white_label=True,
                    custom_integrations=True,
                    bulk_operations=True,
                    export_formats=["pdf", "docx", "html", "json"],
                    ai_model_version="advanced",
                    data_retention_days=90
                ),
                features=[
                    "Unlimited job searches",
                    "Unlimited applications",
                    "All premium features",
                    "Advanced ML autofill",
                    "24/7 priority support",
                    "Advanced analytics dashboard",
                    "Team collaboration (3 seats)",
                    "API access"
                ],
                is_active=True,
                sort_order=2,
                stripe_price_id=getattr(settings, 'STRIPE_PREMIUM_PRICE_ID', None)
            )
        }
    
    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        payment_method_id: Optional[str] = None
    ) -> Subscription:
        """Create a new subscription"""
        
        # Check existing subscription
        existing = await self.db.subscriptions.find_one({
            "user_id": user_id,
            "status": {"$nin": [SubscriptionStatus.CANCELLED.value, SubscriptionStatus.EXPIRED.value]}
        })
        if existing:
            raise ValueError("User already has an active subscription")
        
        # Get plan
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError("Invalid plan ID")
        
        now = datetime.utcnow()
        subscription_data = {
            "_id": f"sub_{user_id}_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "plan_id": plan_id,
            "status": SubscriptionStatus.ACTIVE.value,
            "billing_interval": plan.billing_interval,
            "current_period_start": now,
            "current_period_end": now + timedelta(days=30),
            "current_usage": {
                "searches": 0,
                "applications": 0,
                "cv_generations": 0,
                "cover_letters": 0,
                "api_calls": 0
            },
            "usage_reset_date": now + timedelta(days=30),
            "created_at": now,
            "updated_at": now
        }
        
        # Handle paid tiers with Stripe
        if plan.tier != SubscriptionTier.FREE and payment_method_id:
            try:
                # Get user
                user = await self.db.users.find_one({"_id": user_id})
                if not user:
                    raise ValueError("User not found")
                
                # Create or get Stripe customer
                if user.get("stripe_customer_id"):
                    customer_id = user["stripe_customer_id"]
                else:
                    customer = await self.stripe_client.create_customer(
                        email=user["email"],
                        name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user["email"],
                        metadata={"user_id": user_id}
                    )
                    customer_id = customer["id"]
                    
                    # Update user with Stripe customer ID
                    await self.db.users.update_one(
                        {"_id": user_id},
                        {"$set": {"stripe_customer_id": customer_id}}
                    )
                
                # Attach payment method
                await self.stripe_client.attach_payment_method(
                    customer_id,
                    payment_method_id
                )
                
                # Create Stripe subscription
                stripe_subscription = await self.stripe_client.create_subscription(
                    customer_id=customer_id,
                    price_id=plan.stripe_price_id,
                    trial_period_days=plan.trial_period_days,
                    metadata={"user_id": user_id, "plan_id": plan_id}
                )
                
                subscription_data.update({
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": stripe_subscription["id"],
                    "current_period_start": datetime.fromtimestamp(
                        stripe_subscription["current_period_start"]
                    ),
                    "current_period_end": datetime.fromtimestamp(
                        stripe_subscription["current_period_end"]
                    ),
                    "payment_method_id": payment_method_id
                })
                
                if plan.trial_period_days > 0:
                    subscription_data["trial_start"] = now
                    subscription_data["trial_end"] = now + timedelta(days=plan.trial_period_days)
                    subscription_data["status"] = SubscriptionStatus.TRIALING.value
                
            except Exception as e:
                logger.error(f"Stripe subscription creation failed: {e}")
                raise ValueError(f"Payment setup failed: {str(e)}")
        
        # Insert subscription
        await self.db.subscriptions.insert_one(subscription_data)
        
        # Update user tier
        await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"subscription_tier": plan.tier.value}}
        )
        
        logger.info(f"Created subscription {subscription_data['_id']} for user {user_id}")
        
        # Convert _id to id for response
        subscription_data["id"] = subscription_data["_id"]
        return Subscription(**subscription_data)
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        sub_data = await self.db.subscriptions.find_one({"_id": subscription_id})
        if sub_data:
            sub_data["id"] = sub_data.get("_id")
            return Subscription(**sub_data)
        return None
    
    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription or create free one"""
        try:
            logger.debug(f"get_user_subscription called for user_id: {user_id}")
            
            sub_data = await self.db.subscriptions.find_one({
                "user_id": user_id,
                "status": {"$nin": [SubscriptionStatus.CANCELLED.value, SubscriptionStatus.EXPIRED.value]}
            })
            
            logger.debug(f"Database query result: {sub_data is not None}")
            
            if sub_data:
                logger.debug(f"Found subscription: _id={sub_data.get('_id')}, plan_id={sub_data.get('plan_id')}")
                
                # CRITICAL FIX: Convert ObjectId fields to strings
                sub_data["id"] = str(sub_data.get("_id"))
                
                # Convert user_id if it's an ObjectId
                if isinstance(sub_data.get("user_id"), ObjectId):
                    sub_data["user_id"] = str(sub_data["user_id"])
                    logger.debug(f"Converted user_id from ObjectId to string: {sub_data['user_id']}")
                
                # Convert any other ObjectId fields to strings
                for field in ["stripe_customer_id", "payment_method_id"]:
                    if field in sub_data and isinstance(sub_data[field], ObjectId):
                        sub_data[field] = str(sub_data[field])
                
                # Ensure required datetime fields exist
                from datetime import datetime
                now = datetime.utcnow()
                if "created_at" not in sub_data:
                    sub_data["created_at"] = now
                if "updated_at" not in sub_data:
                    sub_data["updated_at"] = now
                if "current_period_start" not in sub_data:
                    sub_data["current_period_start"] = now
                if "current_period_end" not in sub_data:
                    sub_data["current_period_end"] = now + timedelta(days=30)
                
                # Ensure current_usage exists
                if "current_usage" not in sub_data:
                    sub_data["current_usage"] = {}
                
                try:
                    subscription = Subscription(**sub_data)
                    logger.debug("Successfully created Subscription object")
                    return subscription
                except Exception as e:
                    logger.error(f"Failed to create Subscription object: {e}")
                    logger.error(f"Sub_data keys: {list(sub_data.keys())}")
                    logger.error(f"user_id type: {type(sub_data.get('user_id'))}")
                    raise
            
            # Auto-create free subscription if none exists
            logger.info(f"No subscription found for user {user_id}, attempting to create free subscription")
            try:
                return await self.create_subscription(user_id, "plan_free")
            except Exception as e:
                logger.error(f"Failed to auto-create subscription: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error in get_user_subscription: {e}", exc_info=True)
            return None
    
    async def upgrade_subscription(
        self,
        user_id: str,
        new_plan_id: str,
        payment_method_id: Optional[str] = None
    ) -> Subscription:
        """Upgrade user's subscription"""
        
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            # Create new subscription if none exists
            return await self.create_subscription(user_id, new_plan_id, payment_method_id)
        
        new_plan = await self.get_plan(new_plan_id)
        if not new_plan:
            raise ValueError("Invalid plan")
        
        current_plan = await self.get_plan(subscription.plan_id)
        
        # Check if it's actually an upgrade
        if current_plan and new_plan.price.amount <= current_plan.price.amount:
            raise ValueError("New plan must be higher tier than current plan")
        
        # If upgrading to paid tier
        if new_plan.tier != SubscriptionTier.FREE:
            if not subscription.stripe_subscription_id:
                # Create new Stripe subscription
                if not payment_method_id:
                    raise ValueError("Payment method required for upgrade")
                
                user = await self.db.users.find_one({"_id": user_id})
                customer_id = subscription.stripe_customer_id or user.get("stripe_customer_id")
                
                if not customer_id:
                    customer = await self.stripe_client.create_customer(
                        email=user["email"],
                        name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user["email"],
                        metadata={"user_id": user_id}
                    )
                    customer_id = customer["id"]
                    
                    await self.db.users.update_one(
                        {"_id": user_id},
                        {"$set": {"stripe_customer_id": customer_id}}
                    )
                
                await self.stripe_client.attach_payment_method(customer_id, payment_method_id)
                
                stripe_subscription = await self.stripe_client.create_subscription(
                    customer_id=customer_id,
                    price_id=new_plan.stripe_price_id,
                    metadata={"user_id": user_id, "plan_id": new_plan_id}
                )
                
                update_data = {
                    "plan_id": new_plan_id,
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": stripe_subscription["id"],
                    "payment_method_id": payment_method_id,
                    "status": SubscriptionStatus.ACTIVE.value,
                    "updated_at": datetime.utcnow()
                }
            else:
                # Update existing Stripe subscription
                await self.stripe_client.update_subscription(
                    subscription.stripe_subscription_id,
                    price_id=new_plan.stripe_price_id
                )
                
                update_data = {
                    "plan_id": new_plan_id,
                    "status": SubscriptionStatus.ACTIVE.value,
                    "updated_at": datetime.utcnow()
                }
        else:
            # Downgrading to free
            if subscription.stripe_subscription_id:
                await self.stripe_client.cancel_subscription(
                    subscription.stripe_subscription_id,
                    cancel_immediately=False
                )
            
            update_data = {
                "plan_id": new_plan_id,
                "cancel_at_period_end": True,
                "updated_at": datetime.utcnow()
            }
        
        # Update subscription
        await self.db.subscriptions.update_one(
            {"_id": subscription.id},
            {"$set": update_data}
        )
        
        # Update user tier
        await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"subscription_tier": new_plan.tier.value}}
        )
        
        logger.info(f"Upgraded subscription {subscription.id} to plan {new_plan_id}")
        return await self.get_subscription(subscription.id)
    
    async def cancel_subscription(
        self,
        user_id: str,
        cancel_immediately: bool = False,
        reason: Optional[str] = None
    ) -> Subscription:
        """Cancel user's subscription"""
        
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            raise ValueError("No subscription found")
        
        now = datetime.utcnow()
        update_data = {
            "cancelled_at": now,
            "cancellation_reason": reason,
            "updated_at": now
        }
        
        if cancel_immediately:
            update_data["status"] = SubscriptionStatus.CANCELLED.value
            
            # Update user to free tier
            await self.db.users.update_one(
                {"_id": user_id},
                {"$set": {"subscription_tier": SubscriptionTier.FREE.value}}
            )
            
            if subscription.stripe_subscription_id:
                await self.stripe_client.cancel_subscription(
                    subscription.stripe_subscription_id,
                    cancel_immediately=True
                )
        else:
            update_data["cancel_at_period_end"] = True
            
            if subscription.stripe_subscription_id:
                await self.stripe_client.cancel_subscription(
                    subscription.stripe_subscription_id,
                    cancel_immediately=False
                )
        
        await self.db.subscriptions.update_one(
            {"_id": subscription.id},
            {"$set": update_data}
        )
        
        logger.info(f"Cancelled subscription {subscription.id}")
        return await self.get_subscription(subscription.id)
    
    async def track_usage(
        self,
        user_id: str,
        event_type: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageEvent:
        """Track usage event"""
        
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            raise ValueError("No subscription found")
        
        usage_event = {
            "_id": f"usage_{user_id}_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "subscription_id": subscription.id,
            "event_type": event_type,
            "quantity": quantity,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
            "billing_period_start": subscription.current_period_start,
            "billing_period_end": subscription.current_period_end
        }
        
        await self.db.usage_events.insert_one(usage_event)
        
        # Map event types to usage fields
        usage_field_map = {
            "job_search": "searches",
            "application": "applications",
            "cv_generation": "cv_generations",
            "cover_letter": "cover_letters",
            "api_call": "api_calls"
        }
        
        usage_field = usage_field_map.get(event_type, event_type)
        
        # Update current usage
        usage_key = f"current_usage.{usage_field}"
        await self.db.subscriptions.update_one(
            {"_id": subscription.id},
            {"$inc": {usage_key: quantity}}
        )
        
        usage_event["id"] = usage_event["_id"]
        return UsageEvent(**usage_event)
    
    async def check_usage_limit(
        self,
        user_id: str,
        event_type: str,
        quantity: int = 1
    ) -> tuple[bool, int, int]:
        """Check if user has available usage. Returns (allowed, current, limit)"""
        
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            return False, 0, 0
        
        plan = await self.get_plan(subscription.plan_id)
        if not plan or not plan.limits:
            return True, 0, 9999  # No limits defined
        
        # Map event types to limit fields and usage fields
        limit_map = {
            "job_search": ("monthly_job_searches", "searches"),
            "application": ("monthly_applications", "applications"),
            "cv_generation": ("monthly_cv_generations", "cv_generations"),
            "cover_letter": ("monthly_cover_letters", "cover_letters")
        }
        
        if event_type not in limit_map:
            return True, 0, 9999  # No limit for this event type
        
        limit_field, usage_field = limit_map[event_type]
        
        # Get limit
        limit_obj = getattr(plan.limits, limit_field, None)
        if not limit_obj:
            return True, 0, 9999
        
        limit = limit_obj.max_value
        
        # Get current usage
        current_usage = subscription.current_usage.get(usage_field, 0)
        
        # Check if adding quantity would exceed limit
        allowed = (current_usage + quantity) <= limit
        
        return allowed, current_usage, limit
    
    async def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get subscription plan by ID or tier"""
        # First try to get by tier enum
        for tier, plan in self.PLANS.items():
            if plan.id == plan_id or tier.value == plan_id:
                return plan
        
        # Try to match by plan ID prefix
        if plan_id.startswith("plan_"):
            tier_name = plan_id.replace("plan_", "").upper()
            try:
                tier = SubscriptionTier(tier_name.lower())
                return self.PLANS.get(tier)
            except ValueError:
                pass
        
        return None
    
    async def list_plans(self) -> List[SubscriptionPlan]:
        """List all available plans"""
        return sorted(
            self.PLANS.values(),
            key=lambda x: x.sort_order
        )
    
    async def reset_monthly_usage(self):
        """Reset monthly usage for all subscriptions (run via cron)"""
        now = datetime.utcnow()
        
        # Find subscriptions needing reset
        result = await self.db.subscriptions.update_many(
            {
                "usage_reset_date": {"$lte": now},
                "status": {"$in": [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value]}
            },
            {
                "$set": {
                    "current_usage": {
                        "searches": 0,
                        "applications": 0,
                        "cv_generations": 0,
                        "cover_letters": 0,
                        "api_calls": 0
                    },
                    "usage_reset_date": now + timedelta(days=30),
                    "updated_at": now
                }
            }
        )
        
        logger.info(f"Reset usage for {result.modified_count} subscriptions")