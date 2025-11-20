# backend/app/integrations/stripe_client.py

import stripe
from typing import Dict, Any, Optional
import logging
from app.config import settings
from app.models.user import SubscriptionTier
from app.models.subscription import Money

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeClient:
    """Stripe integration client"""
    
    # Stripe Price IDs for each tier (you'll need to create these in Stripe Dashboard)
    PRICE_IDS = {
        SubscriptionTier.FREE: None,  # Free tier has no price
        SubscriptionTier.BASIC: settings.STRIPE_BASIC_PRICE_ID if hasattr(settings, 'STRIPE_BASIC_PRICE_ID') else None,
        SubscriptionTier.PREMIUM: settings.STRIPE_PREMIUM_PRICE_ID if hasattr(settings, 'STRIPE_PREMIUM_PRICE_ID') else None,
    }
    
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
    
    async def create_customer(
        self,
        email: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise
    
    async def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Attach payment method to customer"""
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")
            return payment_method
        except stripe.error.StripeError as e:
            logger.error(f"Payment method attachment failed: {e}")
            raise
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_period_days: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Stripe subscription"""
        try:
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': metadata or {},
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent']
            }
            
            if trial_period_days > 0:
                subscription_params['trial_period_days'] = trial_period_days
            
            subscription = stripe.Subscription.create(**subscription_params)
            logger.info(f"Created Stripe subscription: {subscription.id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Subscription creation failed: {e}")
            raise
    
    async def update_subscription(
        self,
        subscription_id: str,
        price_id: Optional[str] = None,
        cancel_at_period_end: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update a Stripe subscription"""
        try:
            update_params = {}
            
            if price_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                update_params['items'] = [{
                    'id': subscription['items']['data'][0].id,
                    'price': price_id
                }]
                update_params['proration_behavior'] = 'always_invoice'
            
            if cancel_at_period_end is not None:
                update_params['cancel_at_period_end'] = cancel_at_period_end
            
            if metadata:
                update_params['metadata'] = metadata
            
            subscription = stripe.Subscription.modify(
                subscription_id,
                **update_params
            )
            logger.info(f"Updated Stripe subscription: {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Subscription update failed: {e}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_immediately: bool = False
    ) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        try:
            if cancel_immediately:
                subscription = stripe.Subscription.delete(subscription_id)
                logger.info(f"Immediately cancelled subscription: {subscription_id}")
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Scheduled subscription cancellation: {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Subscription cancellation failed: {e}")
            raise
    
    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a payment intent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Payment intent creation failed: {e}")
            raise
    
    async def create_invoice(
        self,
        customer_id: str,
        subscription_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an invoice"""
        try:
            invoice = stripe.Invoice.create(
                customer=customer_id,
                subscription=subscription_id,
                metadata=metadata or {},
                auto_advance=True
            )
            return invoice
        except stripe.error.StripeError as e:
            logger.error(f"Invoice creation failed: {e}")
            raise
    
    async def retrieve_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Retrieve an invoice"""
        try:
            return stripe.Invoice.retrieve(invoice_id)
        except stripe.error.StripeError as e:
            logger.error(f"Invoice retrieval failed: {e}")
            raise
    
    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a refund"""
        try:
            refund_params = {'payment_intent': payment_intent_id}
            if amount:
                refund_params['amount'] = amount
            if reason:
                refund_params['reason'] = reason
            
            refund = stripe.Refund.create(**refund_params)
            logger.info(f"Created refund: {refund.id}")
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Refund creation failed: {e}")
            raise
    
    async def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Dict[str, Any]:
        """Create a customer portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Portal session creation failed: {e}")
            raise
    
    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a checkout session"""
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Checkout session creation failed: {e}")
            raise
    
    def get_price_id_for_tier(self, tier: SubscriptionTier) -> Optional[str]:
        """Get Stripe price ID for subscription tier"""
        return self.PRICE_IDS.get(tier)
    
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> Dict[str, Any]:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise