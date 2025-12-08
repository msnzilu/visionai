# backend/app/integrations/paystack_client.py

import httpx
from typing import Dict, Any, Optional
import logging
import hashlib
import hmac
from app.core.config import settings
from app.models.user import SubscriptionTier

logger = logging.getLogger(__name__)

class PaystackClient:
    """Paystack integration client"""
    
    BASE_URL = "https://api.paystack.co"
    
    # Plan Codes (Configure these in Paystack Dashboard)
    # You should set these in your .env or config
    PLAN_CODES = {
        SubscriptionTier.FREE: None,
        SubscriptionTier.BASIC: getattr(settings, 'PAYSTACK_BASIC_PLAN_CODE', None),
        SubscriptionTier.PREMIUM: getattr(settings, 'PAYSTACK_PREMIUM_PLAN_CODE', None),
    }
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
    
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an async request to Paystack API"""
        url = f"{self.BASE_URL}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, json=data, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Paystack API error: {e.response.text}")
                # Try to parse error message from Paystack
                try:
                    error_data = e.response.json()
                    raise ValueError(error_data.get("message", "Paystack request failed"))
                except:
                    raise ValueError(f"Paystack request failed: {e}")
            except httpx.RequestError as e:
                logger.error(f"Paystack connection error: {e}")
                raise ValueError(f"Paystack connection error: {e}")

    async def create_customer(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create or update a Paystack customer"""
        data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "metadata": metadata or {}
        }
        if phone:
            data["phone"] = phone
            
        result = await self._request("POST", "/customer", data)
        logger.info(f"Created/Updated Paystack customer: {result['data']['customer_code']}")
        return result['data']

    async def initialize_transaction(
        self,
        email: str,
        amount: int,  # Amount in kobo (or lowest currency unit)
        plan: Optional[str] = None,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize a transaction"""
        data = {
            "email": email,
            "amount": amount,
            "metadata": metadata or {},
        }
        if plan:
            data["plan"] = plan
        if callback_url:
            data["callback_url"] = callback_url
        if reference:
            data["reference"] = reference
            
        result = await self._request("POST", "/transaction/initialize", data)
        logger.info(f"Initialized Paystack transaction: {result['data']['reference']}")
        return result['data']

    async def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify a transaction"""
        result = await self._request("GET", f"/transaction/verify/{reference}")
        logger.info(f"Verified Paystack transaction: {reference}")
        return result['data']
        
    async def fetch_subscription(self, code: str) -> Dict[str, Any]:
        """Fetch a subscription"""
        result = await self._request("GET", f"/subscription/{code}")
        return result['data']

    async def disable_subscription(self, code: str, token: str) -> Dict[str, Any]:
        """Disable a subscription"""
        # Note: 'token' is the email token, code is subscription code
        data = {
            "code": code,
            "token": token
        }
        result = await self._request("POST", "/subscription/disable", data)
        logger.info(f"Disabled Paystack subscription: {code}")
        return result['data']

    async def manage_subscription(self, code: str) -> str:
        """
        Paystack puts subscription management link in the email or via dashboard.
        API can generate a link for update card (not direct cancel typically exposed to API in same way as Stripe Portal).
        However, there is an endpoint to generate a link to update card details.
        """
        # For managing (canceling), we might just use our own UI calling disable_subscription.
        # For updating card, send instruction or use Paystack's built-in emails.
        # Here we return a dummy link or instructions if needed, 
        # but realistically we just handle cancel via API.
        return ""

    def get_plan_code_for_tier(self, tier: SubscriptionTier) -> Optional[str]:
        """Get Paystack plan code for subscription tier"""
        return self.PLAN_CODES.get(tier)

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> bool:
        """Verify Paystack webhook signature"""
        if not webhook_secret:
            return False
            
        hash = hmac.new(
            key=webhook_secret.encode('utf-8'),
            msg=payload,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        return hash == signature
