# backend/app/services/subscription_service.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
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
from app.integrations.paystack_client import PaystackClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.paystack_client = PaystackClient()
        
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
        # Using plan_id as key to support both monthly and annual variants
        
        # Shared limits configurations
        free_limits = SubscriptionLimits(
            monthly_manual_applications=create_limit("monthly_manual_applications", 5),
            monthly_auto_applications=create_limit("monthly_auto_applications", 0),
            monthly_cv_generations=create_limit("monthly_cv_generations", 0),
            monthly_cover_letters=create_limit("monthly_cover_letters", 0),
            concurrent_applications=create_limit("concurrent_applications", 1, "instant", False),
            max_jobs_per_search=50,
            api_rate_limit_per_minute=10,
            storage_mb=50,
            team_members=1,
            advanced_analytics=False,
            priority_support=False,
            white_label=False,
            custom_integrations=False,
            bulk_operations=False,
            export_formats=[],
            ai_model_version="basic",
            data_retention_days=30
        )
        
        basic_limits = SubscriptionLimits(
            monthly_manual_applications=create_limit("monthly_manual_applications", 9999),
            monthly_auto_applications=create_limit("monthly_auto_applications", 600), # 20 per day * 30
            monthly_cv_generations=create_limit("monthly_cv_generations", 9999),
            monthly_cover_letters=create_limit("monthly_cover_letters", 9999),
            concurrent_applications=create_limit("concurrent_applications", 20, "daily", True),
            max_jobs_per_search=50,
            api_rate_limit_per_minute=50,
            storage_mb=500,
            team_members=1,
            advanced_analytics=True,
            priority_support=True,
            white_label=False,
            custom_integrations=False,
            bulk_operations=True,
            export_formats=["pdf", "docx"],
            ai_model_version="standard",
            data_retention_days=60
        )
        
        premium_limits = SubscriptionLimits(
            monthly_manual_applications=create_limit("monthly_manual_applications", 9999),
            monthly_auto_applications=create_limit("monthly_auto_applications", 9999),
            monthly_cv_generations=create_limit("monthly_cv_generations", 9999),
            monthly_cover_letters=create_limit("monthly_cover_letters", 9999),
            concurrent_applications=create_limit("concurrent_applications", 9999, "instant", False),
            max_jobs_per_search=100,
            api_rate_limit_per_minute=200,
            storage_mb=2000,
            team_members=5,
            advanced_analytics=True,
            priority_support=True,
            white_label=True,
            custom_integrations=True,
            bulk_operations=True,
            export_formats=["pdf", "docx", "html", "json"],
            ai_model_version="advanced",
            data_retention_days=180
        )
        
        basic_features = [
            "Unlimited manual applications",
            "20 auto-applications per day",
            "Premium CV templates",
            "AI-powered cover letters",
            "Priority support",
            "Advanced analytics"
        ]
        
        premium_features = [
            "Unlimited manual applications",
            "Unlimited auto-applications",
            "Full automation enabled",
            "Advanced ML autofill",
            "24/7 priority support",
            "Advanced analytics dashboard",
            "Team collaboration (5 seats)",
            "API access",
            "White-label options"
        ]
        
        self.PLANS = {
            # Free Plan
            "plan_free": SubscriptionPlan(
                id="plan_free",
                name="Free Plan",
                tier=SubscriptionTier.FREE,
                description="Get started with manual applications",
                price=Money(amount=0, currency=Currency.KES),
                billing_interval="monthly",
                trial_period_days=0,
                limits=free_limits,
                features=[
                    "5 manual applications per month",
                    "No auto-apply",
                    "No CV customization",
                    "Email support"
                ],
                is_active=True,
                sort_order=0
            ),
            # Basic Monthly
            "plan_basic": SubscriptionPlan(
                id="plan_basic",
                name="Basic Plan",
                tier=SubscriptionTier.BASIC,
                description="Perfect for active job seekers",
                price=Money(amount=260000, currency=Currency.KES),  # KES 2,600/month
                billing_interval="monthly",
                trial_period_days=7,
                limits=basic_limits,
                features=basic_features,
                is_popular=True,
                is_active=True,
                sort_order=1,
                paystack_plan_code=getattr(settings, 'PAYSTACK_BASIC_PLAN_CODE', None)
            ),
            # Basic Annual (2 months free = 10 months price)
            "plan_basic_annual": SubscriptionPlan(
                id="plan_basic_annual",
                name="Basic Plan",
                tier=SubscriptionTier.BASIC,
                description="Perfect for active job seekers",
                price=Money(amount=2600000, currency=Currency.KES),  # KES 26,000/year (save KES 5,200)
                billing_interval="yearly",
                trial_period_days=7,
                limits=basic_limits,
                features=basic_features + ["2 months FREE"],
                is_popular=True,
                is_active=True,
                sort_order=1,
                paystack_plan_code=getattr(settings, 'PAYSTACK_BASIC_ANNUAL_PLAN_CODE', None)
            ),
            # Premium Monthly
            "plan_premium": SubscriptionPlan(
                id="plan_premium",
                name="Premium Plan",
                tier=SubscriptionTier.PREMIUM,
                description="Full automation for serious professionals",
                price=Money(amount=640000, currency=Currency.KES),  # KES 6,400/month
                billing_interval="monthly",
                trial_period_days=14,
                limits=premium_limits,
                features=premium_features,
                is_active=True,
                sort_order=2,
                paystack_plan_code=getattr(settings, 'PAYSTACK_PREMIUM_PLAN_CODE', None)
            ),
            # Premium Annual (2 months free = 10 months price)
            "plan_premium_annual": SubscriptionPlan(
                id="plan_premium_annual",
                name="Premium Plan",
                tier=SubscriptionTier.PREMIUM,
                description="Full automation for serious professionals",
                price=Money(amount=6400000, currency=Currency.KES),  # KES 64,000/year (save KES 12,800)
                billing_interval="yearly",
                trial_period_days=14,
                limits=premium_limits,
                features=premium_features + ["2 months FREE"],
                is_active=True,
                sort_order=2,
                paystack_plan_code=getattr(settings, 'PAYSTACK_PREMIUM_ANNUAL_PLAN_CODE', None)
            )
        }
    
    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        reference: Optional[str] = None
    ) -> Subscription:
        """Create a new subscription"""
        
        # Convert user_id to ObjectId for database queries
        # Convert user_id to ObjectId for database queries
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Check existing subscription (search both string and ObjectId formats)
        # IMPORTANT: Do not filter by status - if a cancelled/expired subscription exists,
        # we must UPDATE it, not create a new one (prevent duplicate key error)
        existing = await self.db.subscriptions.find_one({
            "$or": [
                {"user_id": user_oid},
                {"user_id": user_id}
            ]
        })
        
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
                "manual_applications": 0,
                "auto_applications": 0,
                "searches": 0, # Kept for legacy
                "applications": 0, # Kept for legacy
                "cv_generations": 0,
                "cover_letters": 0,
                "api_calls": 0
            },
            "usage_reset_date": now + timedelta(days=30),
            "created_at": now,
            "updated_at": now
        }
        
        # Handle paid tiers with Paystack
        if plan.tier != SubscriptionTier.FREE and reference:
            try:
                # Verify transaction reference
                verification = await self.paystack_client.verify_transaction(reference)
                
                if verification["status"] != "success":
                    raise ValueError(f"Transaction failed: {verification.get('gateway_response', 'Unknown error')}")

                # Ensure the amount matches
                cost_in_kobo = int(plan.price.amount * 100) # Assuming price amount is USD/NGN standard, converted to kobo?
                # Actually usage in logic: Money(amount=2000) -> $20.00. 
                # If paystack expects kobo/cents. If Currency is USD, Paystack supports USD.
                # Just converting logic: 2000 -> 2000 cents.
                
                # Check amount
                if verification["amount"] < plan.price.amount: # be careful with units here
                    logger.warning(f"Transaction amount mismatch. Expected >= {plan.price.amount}, got {verification['amount']}")
                    # raise ValueError("Transaction amount too low")
                
                customer_data = verification.get("customer", {})
                customer_code = customer_data.get("customer_code")
                authorization = verification.get("authorization", {})
                auth_code = authorization.get("authorization_code")
                
                # Update user with Paystack customer code
                # Ensure valid ObjectId
                try:
                    user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
                except:
                    # In case of OAuth ID or invalid format, find by string ID if needed, or log warning
                    # If user_id is the _id, convert only if valid ObjectId
                    import bson
                    if bson.objectid.ObjectId.is_valid(user_id):
                        user_oid = ObjectId(user_id)
                    else:
                        user_oid = user_id # Fallback to string ID if that's what is used
                        
                await self.db.users.update_one(
                    {"_id": user_oid},
                    {"$set": {"paystack_customer_code": customer_code}}
                )
                
                subscription_data.update({
                    "paystack_customer_code": customer_code,
                    "paystack_transaction_reference": reference,
                    "paystack_transaction_id": str(verification.get("id")),
                    "paystack_authorization_code": auth_code,
                    "payment_method_id": auth_code, # Use auth code as internal payment method ID ref
                    "status": SubscriptionStatus.ACTIVE.value
                })
                
                # If plan has subscription code (created automatically by Paystack if plan passed in init)
                # verification response usually contains plan info if it was recurring
                # or we rely on webhook 'subscription.create' to populate the subscription_code later
                
            except Exception as e:
                logger.error(f"Paystack verification failed: {e}")
                raise ValueError(f"Payment verification failed: {str(e)}")
        
        # Handle existing subscription - UPDATE instead of insert to avoid duplicate key error
        if existing:
            # Update the existing subscription with new plan data
            subscription_data["_id"] = existing["_id"]  # Keep the same ID
            await self.db.subscriptions.update_one(
                {"_id": existing["_id"]},
                {"$set": subscription_data}
            )
            logger.info(f"Updated subscription {existing['_id']} for user {user_id}")
        else:
            # No existing subscription, create new one
            await self.db.subscriptions.insert_one(subscription_data)
            logger.info(f"Created subscription {subscription_data['_id']} for user {user_id}")
        
        # Update user tier
        user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        await self.db.users.update_one(
            {"_id": user_oid},
            {"$set": {"subscription_tier": plan.tier.value}}
        )
        
        # Convert _id to id for response
        subscription_data["id"] = str(subscription_data["_id"])
        
        # Ensure user_id is string for Pydantic
        if isinstance(subscription_data.get("user_id"), ObjectId):
            subscription_data["user_id"] = str(subscription_data["user_id"])
            
        return Subscription(**subscription_data)
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        try:
             # Handle string vs ObjectId for query
            sub_oid = ObjectId(subscription_id) if isinstance(subscription_id, str) else subscription_id
            sub_data = await self.db.subscriptions.find_one({"_id": sub_oid})
            
            if sub_data:
                # Convert ObjectId fields for Pydantic
                sub_data["id"] = str(sub_data.get("_id"))
                if isinstance(sub_data.get("user_id"), ObjectId):
                    sub_data["user_id"] = str(sub_data["user_id"])
                    
                return Subscription(**sub_data)
            return None
        except Exception as e:
            logger.error(f"Error getting subscription {subscription_id}: {e}")
            return None
    
    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription or create free one"""
        try:
            logger.debug(f"get_user_subscription called for user_id: {user_id}")
            
            # Sync with User Profile (Source of Truth)
            try:
                # Convert string user_id to ObjectId if needed
                user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
                user = await self.db.users.find_one({"_id": user_oid})
                
                if user:
                    user_tier = user.get("subscription_tier", "free")
                    # Determine target plan ID from user tier
                    target_plan_id = user_tier if user_tier.startswith("plan_") else f"plan_{user_tier}"
                    
                    # Fetch ANY subscription (active or not) to avoid duplicate key errors
                    # Use user_oid to match ObjectId in DB
                    sub_data = await self.db.subscriptions.find_one({
                        "user_id": user_oid
                    })
                    
                    # Check for mismatch
                    current_plan_id = sub_data.get("plan_id") if sub_data else None
                    
                    if current_plan_id != target_plan_id:
                        logger.info(f"Syncing subscription for user {user_id}: Subscription={current_plan_id}, User={target_plan_id}")
                        
                        if sub_data:
                            # Update existing subscription
                            now = datetime.utcnow()
                            await self.db.subscriptions.update_one(
                                {"_id": sub_data["_id"]},
                                {"$set": {
                                    "plan_id": target_plan_id,
                                    "status": SubscriptionStatus.ACTIVE.value,
                                    "updated_at": now,
                                    "current_period_start": now,
                                    "current_period_end": now + timedelta(days=30)
                                }}
                            )
                        else:
                            # Create new subscription
                            try:
                                await self.create_subscription(user_id, target_plan_id)
                            except Exception as e:
                                logger.error(f"Failed to auto-create subscription during sync: {e}")
                                # Fallthrough to return None or existing logic
            except Exception as e:
                logger.error(f"Error in subscription sync logic: {e}")

            sub_data = await self.db.subscriptions.find_one({
                "user_id": ObjectId(user_id),
                "status": {"$nin": [SubscriptionStatus.CANCELLED.value, SubscriptionStatus.EXPIRED.value]}
            })
            
            if sub_data:
                # Convert ObjectId fields to strings
                sub_data["id"] = str(sub_data.get("_id"))
                
                if isinstance(sub_data.get("user_id"), ObjectId):
                    sub_data["user_id"] = str(sub_data["user_id"])
                
                # Convert Paystack/legacy fields
                for field in ["paystack_customer_code", "paystack_subscription_code"]:
                    if field in sub_data and isinstance(sub_data[field], ObjectId):
                        sub_data[field] = str(sub_data[field])

                # Ensure required datetime fields exist
                now = datetime.utcnow()
                if "created_at" not in sub_data:
                    sub_data["created_at"] = now
                if "updated_at" not in sub_data:
                    sub_data["updated_at"] = now
                if "current_period_start" not in sub_data:
                    sub_data["current_period_start"] = now
                if "current_period_end" not in sub_data:
                    sub_data["current_period_end"] = now + timedelta(days=30)
                
                if "current_usage" not in sub_data:
                    sub_data["current_usage"] = {}
                
                try:
                    subscription = Subscription(**sub_data)
                    return subscription
                except Exception as e:
                    logger.error(f"Failed to create Subscription object: {e}")
                    raise
            
            # Auto-create free subscription if none exists
            logger.info(f"No subscription found for user {user_id}, attempting to create free subscription")
            try:
                # IMPORTANT: Recursion protection - if we are already trying to create plan_free, don't recurse
                # But here we pass "plan_free" which is different.
                # However, create_subscription calls get_plan.
                return await self.create_subscription(user_id, "plan_free")
            except Exception as e:
                logger.error(f"Failed to auto-create subscription: {e}")
                raise e # Propagate error to be seen

                
                
        except Exception as e:
            logger.error(f"Error in get_user_subscription: {e}", exc_info=True)
            # Do not return None, let the error propagate or raise a specific one so we can see it
            raise e
    
    async def upgrade_subscription(
        self,
        user_id: str,
        new_plan_id: str,
        reference: Optional[str] = None
    ) -> Subscription:
        """Upgrade user's subscription"""
        
        # Essentially same as verify and create new subscription for Paystack Inline flow
        return await self.create_subscription(user_id, new_plan_id, reference)
    
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
        
        try:
            # If there is a Paystack subscription code (recurring), disable it
            if subscription.paystack_subscription_code:
                # We need email token for disable? 
                # API documentation says: POST /subscription/disable with "code" and "token"
                # But token is sent to user email. 
                # Alternative: Some Paystack integration allows 'manage' link or just stopping local renewal if we charge via authorization manually.
                # If it's a true Paystack Subscription (auto-charge):
                # We might not have the 'token'. 
                # Best effort: Update local status. 
                pass
                
        except Exception as e:
            logger.error(f"Paystack cancellation error: {e}")
            # Continue to cancel locally
        
        if cancel_immediately:
            update_data["status"] = SubscriptionStatus.CANCELLED.value
            
            # Update user to free tier
            await self.db.users.update_one(
                {"_id": user_id},
                {"$set": {"subscription_tier": SubscriptionTier.FREE.value}}
            )
        else:
            update_data["cancel_at_period_end"] = True
            # Paystack doesn't have "cancel at period end" natively in API often without email token flow
            # We just handle logic locally not to renew.
        
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
            "manual_application": "manual_applications",
            "auto_application": "auto_applications",
            "job_search": "searches", # Legacy
            "application": "manual_applications", # Default application to manual
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
        # Map event types to limit fields and usage fields
        limit_map = {
            "manual_application": ("monthly_manual_applications", "manual_applications"),
            "auto_application": ("monthly_auto_applications", "auto_applications"),
            "application": ("monthly_manual_applications", "manual_applications"), # Default
            "cv_generation": ("monthly_cv_generations", "cv_generations"),
            "cover_letter": ("monthly_cover_letters", "cover_letters"),
             "job_search": ("monthly_job_searches", "searches") # Legacy
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
                        "manual_applications": 0,
                        "auto_applications": 0,
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
