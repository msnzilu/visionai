# backend/app/services/referral_service.py

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import uuid
import secrets
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.subscription import Referral, ReferralProgram, Money
from app.models.user import SubscriptionTier
from app.models.common import Currency

logger = logging.getLogger(__name__)

class ReferralService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
        # Referral rewards: 5 applications (manual + auto) per 5 paid referrals
        self.REFERRAL_REWARDS = {
            "applications_per_milestone": 5,  # 5 bonus apps per milestone
            "milestone_referrals": 5,  # Every 5 paid referrals
            "paid_tiers": [SubscriptionTier.BASIC.value, SubscriptionTier.PREMIUM.value]
        }
    
    def generate_referral_code(self, user_id: str) -> str:
        """Generate unique referral code"""
        # Create a user-friendly referral code
        random_part = secrets.token_urlsafe(6).upper().replace('-', '').replace('_', '')
        return f"{user_id[:4].upper()}{random_part[:6]}"
    
    async def create_referral_program(
        self,
        name: str,
        description: str,
        referrer_reward_amount: int,
        referee_reward_amount: int,
        valid_until: Optional[datetime] = None
    ) -> ReferralProgram:
        """Create a referral program"""
        
        program_data = {
            "_id": f"prog_{uuid.uuid4().hex[:8]}",
            "name": name,
            "description": description,
            "is_active": True,
            "referrer_reward_type": "credit",
            "referrer_reward_amount": Money(amount=referrer_reward_amount, currency=Currency.USD),
            "referee_reward_type": "discount",
            "referee_reward_amount": Money(amount=referee_reward_amount, currency=Currency.USD),
            "minimum_subscription_duration": 30,
            "maximum_rewards_per_user": None,
            "valid_from": datetime.utcnow(),
            "valid_until": valid_until,
            "total_referrals": 0,
            "successful_referrals": 0,
            "total_rewards_paid": Money(amount=0, currency=Currency.USD)
        }
        
        await self.db.referral_programs.insert_one(program_data)
        return ReferralProgram(**program_data)
    
    async def create_referral(
        self,
        referrer_user_id: str,
        referee_email: str,
        program_id: Optional[str] = None
    ) -> Referral:
        """Create a referral"""
        
        # Get or create default program
        if not program_id:
            program = await self.db.referral_programs.find_one({"is_active": True})
            if not program:
                # Create default program
                default_program = await self.create_referral_program(
                    name="Default Referral Program",
                    description="Refer friends and earn rewards",
                    referrer_reward_amount=1000,  # $10 credit
                    referee_reward_amount=500  # $5 discount
                )
                program_id = default_program.id
            else:
                program_id = program["_id"]
        
        # Generate unique referral code
        referral_code = self.generate_referral_code(referrer_user_id)
        
        # Check if referral already exists
        existing = await self.db.referrals.find_one({
            "referrer_user_id": referrer_user_id,
            "referee_email": referee_email
        })
        
        if existing:
            return Referral(**existing)
        
        referral_data = {
            "_id": f"ref_{uuid.uuid4().hex[:8]}",
            "program_id": program_id,
            "referrer_user_id": referrer_user_id,
            "referee_email": referee_email,
            "referral_code": referral_code,
            "status": "pending",
            "referred_at": datetime.utcnow(),
            "referrer_reward_paid": False,
            "referee_reward_paid": False,
            "metadata": {}
        }
        
        await self.db.referrals.insert_one(referral_data)
        
        # Update program stats
        await self.db.referral_programs.update_one(
            {"_id": program_id},
            {"$inc": {"total_referrals": 1}}
        )
        
        logger.info(f"Created referral {referral_data['_id']} for user {referrer_user_id}")
        return Referral(**referral_data)
    
    async def complete_referral(
        self,
        referral_code: str,
        referee_user_id: str
    ) -> Referral:
        """Complete a referral when referee signs up"""
        
        referral = await self.db.referrals.find_one({"referral_code": referral_code})
        if not referral:
            raise ValueError("Invalid referral code")
        
        if referral["status"] != "pending":
            raise ValueError("Referral already completed or expired")
        
        # Update referral
        update_data = {
            "referee_user_id": referee_user_id,
            "status": "completed",
            "completed_at": datetime.utcnow()
        }
        
        await self.db.referrals.update_one(
            {"_id": referral["_id"]},
            {"$set": update_data}
        )
        
        # Update program stats
        await self.db.referral_programs.update_one(
            {"_id": referral["program_id"]},
            {"$inc": {"successful_referrals": 1}}
        )
        
        # Grant referee reward (discount/credit)
        program = await self.db.referral_programs.find_one({"_id": referral["program_id"]})
        if program:
            await self.grant_referee_reward(referee_user_id, program)
            
            await self.db.referrals.update_one(
                {"_id": referral["_id"]},
                {"$set": {"referee_reward_paid": True}}
            )
        
        logger.info(f"Completed referral {referral['_id']}")
        return Referral(**{**referral, **update_data})
    
    async def grant_referrer_reward(
        self,
        referrer_user_id: str,
        referral_id: str
    ):
        """Grant reward to referrer after referee's subscription is active for minimum period"""
        
        referral = await self.db.referrals.find_one({"_id": referral_id})
        if not referral or referral["referrer_reward_paid"]:
            return
        
        program = await self.db.referral_programs.find_one({"_id": referral["program_id"]})
        if not program:
            return
        
        # Count PAID referrals (Basic or Premium subscribers only)
        paid_referrals = await self.db.referrals.count_documents({
            "referrer_user_id": referrer_user_id,
            "status": "completed",
            "referee_user_id": {"$exists": True}
        })
        
        # Get referee's subscription to check if it's paid
        referee_id = referral.get("referee_user_id")
        if referee_id:
            referee = await self.db.users.find_one({"_id": referee_id})
            if referee:
                referee_tier = referee.get("subscription_tier", "free")
                
                # Only count if referee is on paid tier (Basic or Premium)
                if referee_tier in self.REFERRAL_REWARDS["paid_tiers"]:
                    # Calculate milestones reached
                    milestone_referrals = self.REFERRAL_REWARDS["milestone_referrals"]
                    milestones_reached = paid_referrals // milestone_referrals
                    
                    if milestones_reached > 0:
                        # Grant bonus applications
                        bonus_apps = milestones_reached * self.REFERRAL_REWARDS["applications_per_milestone"]
                        
                        # Update user's bonus applications
                        await self.db.users.update_one(
                            {"_id": referrer_user_id},
                            {
                                "$set": {
                                    "referral_bonus_manual_applications": bonus_apps,
                                    "referral_bonus_auto_applications": bonus_apps
                                },
                                "$inc": {"total_referrals": 1}
                            }
                        )
                        
                        logger.info(f"Granted {bonus_apps} bonus applications to user {referrer_user_id} for {paid_referrals} paid referrals")
        
        # Mark reward as paid
        await self.db.referrals.update_one(
            {"_id": referral_id},
            {
                "$set": {
                    "referrer_reward_paid": True,
                    "referrer_reward_amount": Money(
                        amount=program["referrer_reward_amount"]["amount"],
                        currency=Currency.USD
                    )
                }
            }
        )
        
        logger.info(f"Granted referrer reward for referral {referral_id}")
    
    async def grant_referee_reward(
        self,
        referee_user_id: str,
        program: Dict[str, Any]
    ):
        """Grant reward to referee (discount or credit)"""
        
        reward_amount = program["referee_reward_amount"]["amount"]
        
        # Create account credit
        credit_data = {
            "_id": f"credit_{uuid.uuid4().hex[:8]}",
            "user_id": referee_user_id,
            "credit_type": "referral",
            "amount": Money(amount=reward_amount, currency=Currency.USD),
            "description": f"Referral reward - {program['name']}",
            "expires_at": datetime.utcnow() + timedelta(days=90),
            "is_used": False,
            "source": "referral",
            "source_id": program["_id"],
            "created_at": datetime.utcnow()
        }
        
        await self.db.account_credits.insert_one(credit_data)
        logger.info(f"Granted referee reward to user {referee_user_id}")
    
    async def get_user_referrals(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Referral]:
        """Get user's referrals"""
        
        query = {"referrer_user_id": user_id}
        if status:
            query["status"] = status
        
        referrals = await self.db.referrals.find(query).to_list(length=100)
        return [Referral(**ref) for ref in referrals]
    
    async def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's referral statistics"""
        
        total_referrals = await self.db.referrals.count_documents({
            "referrer_user_id": user_id
        })
        
        successful_referrals = await self.db.referrals.count_documents({
            "referrer_user_id": user_id,
            "status": "completed"
        })
        
        pending_referrals = await self.db.referrals.count_documents({
            "referrer_user_id": user_id,
            "status": "pending"
        })
        
        # Count paid referrals (Basic or Premium subscribers)
        paid_referrals_count = 0
        completed_refs = await self.db.referrals.find({
            "referrer_user_id": user_id,
            "status": "completed",
            "referee_user_id": {"$exists": True}
        }).to_list(length=None)
        
        for ref in completed_refs:
            referee_id = ref.get("referee_user_id")
            if referee_id:
                referee = await self.db.users.find_one({"_id": referee_id})
                if referee and referee.get("subscription_tier") in self.REFERRAL_REWARDS["paid_tiers"]:
                    paid_referrals_count += 1
        
        # Get user's bonus applications
        user = await self.db.users.find_one({"_id": user_id})
        bonus_manual_apps = user.get("referral_bonus_manual_applications", 0)
        bonus_auto_apps = user.get("referral_bonus_auto_applications", 0)
        
        # Calculate next milestone
        milestone_referrals = self.REFERRAL_REWARDS["milestone_referrals"]
        next_reward_in = milestone_referrals - (paid_referrals_count % milestone_referrals)
        
        return {
            "total_referrals": total_referrals,
            "successful_referrals": successful_referrals,
            "pending_referrals": pending_referrals,
            "paid_referrals": paid_referrals_count,
            "bonus_manual_applications": bonus_manual_apps,
            "bonus_auto_applications": bonus_auto_apps,
            "bonus_searches_earned": 0,  # Deprecated
            "referral_code": user.get("referral_code"),
            "next_reward_in": next_reward_in if next_reward_in < milestone_referrals else 0
        }
    
    async def validate_referral_code(self, referral_code: str) -> bool:
        """Validate if referral code exists and is active"""
        
        referral = await self.db.referrals.find_one({
            "referral_code": referral_code,
            "status": "pending"
        })
        
        return referral is not None
    
    async def check_referee_eligibility(
        self,
        referee_user_id: str,
        minimum_days: int = 30
    ) -> bool:
        """Check if referee has been subscribed for minimum period"""
        
        subscription = await self.db.subscriptions.find_one({"user_id": referee_user_id})
        if not subscription:
            return False
        
        created_at = subscription.get("created_at")
        if not created_at:
            return False
        
        days_subscribed = (datetime.utcnow() - created_at).days
        return days_subscribed >= minimum_days