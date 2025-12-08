# backend/app/models/subscription.py
"""
Subscription and billing-related Pydantic models
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import uuid

from .common import TimeStampedModel, Money, Currency
from .user import SubscriptionTier


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"


class BillingInterval(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"
    DAILY = "daily"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethodType(str, Enum):
    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    PAYSTACK = "paystack"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class RefundReason(str, Enum):
    DUPLICATE = "duplicate"
    FRAUDULENT = "fraudulent"
    REQUESTED_BY_CUSTOMER = "requested_by_customer"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    SERVICE_NOT_PROVIDED = "service_not_provided"
    OTHER = "other"


# NEW: Add LimitType enum for the fixed UsageLimit
class LimitType(str, Enum):
    """Type of usage limit"""
    COUNT = "count"
    STORAGE = "storage"
    RATE = "rate"


# UPDATED: UsageLimit with both old and new structure support
class UsageLimit(BaseModel):
    """Usage limit configuration - compatible with both old and new structures"""
    name: str
    limit_type: Union[str, LimitType] = LimitType.COUNT
    max_value: int
    period: str = "monthly"  # monthly, daily, weekly, instant
    reset_on_billing: bool = True
    
    # Legacy fields (for backward compatibility)
    current_value: int = 0
    reset_period: Optional[str] = None
    last_reset: Optional[datetime] = None
    is_hard_limit: bool = True
    warning_threshold: Optional[int] = None
    
    @validator('current_value')
    def validate_current_value(cls, v, values):
        max_value = values.get('max_value', 0)
        if v > max_value and values.get('is_hard_limit', True):
            return max_value  # Cap at max instead of raising error
        return v
    
    @validator('limit_type', pre=True)
    def validate_limit_type(cls, v):
        if isinstance(v, str):
            try:
                return LimitType(v)
            except ValueError:
                return LimitType.COUNT
        return v
    
    class Config:
        use_enum_values = True


class FeatureAccess(BaseModel):
    """Feature access configuration"""
    feature_name: str
    is_enabled: bool = True
    usage_limit: Optional[UsageLimit] = None
    configuration: Dict[str, Any] = {}


class SubscriptionLimits(BaseModel):
    """Subscription limits and features"""
    # Core limits - now using the updated UsageLimit structure
    monthly_job_searches: UsageLimit
    monthly_applications: Optional[UsageLimit] = None
    monthly_cv_generations: Optional[UsageLimit] = None
    monthly_cover_letters: Optional[UsageLimit] = None
    concurrent_applications: Optional[UsageLimit] = None
    
    # Legacy fields for backward compatibility
    daily_job_searches: Optional[UsageLimit] = None
    jobs_per_search: Optional[UsageLimit] = None
    cv_customizations: Optional[UsageLimit] = None
    cover_letter_generations: Optional[UsageLimit] = None
    auto_applications: Optional[UsageLimit] = None
    
    # Simple integer limits (not UsageLimit objects)
    max_jobs_per_search: int = 10
    api_rate_limit_per_minute: int = 10
    storage_mb: int = 100
    team_members: int = 1
    
    # Feature flags
    advanced_analytics: bool = False
    priority_support: bool = False
    white_label: bool = False
    custom_integrations: bool = False
    bulk_operations: bool = False
    
    # Additional settings
    export_formats: List[str] = Field(default=["pdf"])
    ai_model_version: str = "basic"
    data_retention_days: int = 30
    
    # Feature access list (optional)
    features: List[FeatureAccess] = []
    
    # Storage limits (optional)
    document_storage_mb: Optional[UsageLimit] = None
    max_saved_jobs: Optional[UsageLimit] = None
    max_job_alerts: Optional[UsageLimit] = None


# Subscription Plan Models
class SubscriptionPlan(BaseModel):
    """Subscription plan definition"""
    id: str
    name: str
    tier: SubscriptionTier
    description: str
    price: Money
    billing_interval: str = "monthly"  # Changed from BillingInterval to str for flexibility
    trial_period_days: int = 0
    limits: SubscriptionLimits
    features: List[str] = []
    is_popular: bool = False
    is_active: bool = True
    sort_order: int = 0
    metadata: Dict[str, Any] = {}
    
    # Paystack integration
    paystack_plan_code: Optional[str] = None
    paystack_product_id: Optional[str] = None


# Payment Method Models
class BillingAddress(BaseModel):
    """Billing address model"""
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str


class PaymentMethod(BaseModel):
    """Payment method model"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    type: PaymentMethodType
    is_default: bool = False
    
    # Card details (for cards)
    card_brand: Optional[str] = None
    card_last_four: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    
    # Billing details
    billing_address: Optional[BillingAddress] = None
    billing_email: Optional[EmailStr] = None
    
    # External provider details
    paystack_authorization_code: Optional[str] = None
    paypal_account_id: Optional[str] = None
    
    # Metadata
    fingerprint: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


# Subscription Models
class SubscriptionBase(BaseModel):
    """Base subscription model"""
    user_id: str
    plan_id: str
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    billing_interval: str = "monthly"
    payment_method_id: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    """Create subscription model"""
    trial_end: Optional[datetime] = None
    promo_code: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None


class SubscriptionUpdate(BaseModel):
    """Update subscription model"""
    plan_id: Optional[str] = None
    status: Optional[SubscriptionStatus] = None
    payment_method_id: Optional[str] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None


class Subscription(SubscriptionBase, TimeStampedModel):
    """Complete subscription model"""
    id: Optional[str] = Field(None, alias="_id")
    
    # Plan and pricing
    plan: Optional[SubscriptionPlan] = None
    current_period_start: datetime = Field(default_factory=datetime.utcnow)
    current_period_end: datetime = Field(default_factory=datetime.utcnow)
    
    # Trial information
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    
    # Cancellation
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    # Usage tracking
    current_usage: Dict[str, int] = {}
    usage_reset_date: Optional[datetime] = None
    
    # External provider data
    paystack_subscription_code: Optional[str] = None
    paystack_customer_code: Optional[str] = None
    
    # Billing
    next_billing_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    payment_failed_count: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = {}
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SubscriptionResponse(BaseModel):
    """Subscription response model"""
    id: str
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool
    current_usage: Dict[str, int]
    next_billing_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# Invoice Models
class InvoiceLineItem(BaseModel):
    """Invoice line item"""
    description: str
    quantity: int = 1
    unit_amount: Money
    total_amount: Money
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    proration: bool = False
    metadata: Dict[str, Any] = {}


class Invoice(BaseModel):
    """Invoice model"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    subscription_id: Optional[str] = None
    
    # Invoice details
    invoice_number: str
    status: InvoiceStatus
    
    # Amounts
    subtotal: Money
    tax_amount: Money = Field(default_factory=lambda: Money(amount=0))
    discount_amount: Money = Field(default_factory=lambda: Money(amount=0))
    total_amount: Money
    amount_paid: Money = Field(default_factory=lambda: Money(amount=0))
    amount_due: Money
    
    # Line items
    line_items: List[InvoiceLineItem] = []
    
    # Dates
    invoice_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    
    # External provider
    paystack_invoice_code: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    
    # Billing information
    billing_address: Optional[BillingAddress] = None
    
    # Metadata
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


# Payment Models
class Payment(BaseModel):
    """Payment model"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    
    # Payment details
    amount: Money
    status: PaymentStatus
    payment_method_id: Optional[str] = None
    
    # External provider
    paystack_transaction_reference: Optional[str] = None
    paystack_transaction_id: Optional[str] = None
    
    # Failure information
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = {}
    
    class Config:
        populate_by_name = True


# Refund Models
class Refund(BaseModel):
    """Refund model"""
    id: Optional[str] = Field(None, alias="_id")
    payment_id: str
    user_id: str
    
    # Refund details
    amount: Money
    reason: RefundReason
    reason_description: Optional[str] = None
    status: str = "pending"
    
    # External provider
    paystack_refund_id: Optional[str] = None
    
    # Dates
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = {}
    
    class Config:
        populate_by_name = True


# Promo Code Models
class PromoCode(BaseModel):
    """Promotional code model"""
    id: Optional[str] = Field(None, alias="_id")
    code: str
    name: str
    description: Optional[str] = None
    
    # Discount details
    discount_type: str = "percentage"
    discount_value: float
    max_redemptions: Optional[int] = None
    current_redemptions: int = 0
    
    # Applicability
    applicable_plans: List[str] = []
    minimum_amount: Optional[Money] = None
    
    # Validity
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    is_active: bool = True
    
    # Usage tracking
    used_by_users: List[str] = []
    
    # Metadata
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


# Subscription Analytics Models
class SubscriptionStats(BaseModel):
    """Subscription statistics"""
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    cancelled_subscriptions: int = 0
    trial_subscriptions: int = 0
    
    # Revenue metrics
    monthly_recurring_revenue: Money = Field(default_factory=lambda: Money(amount=0))
    annual_recurring_revenue: Money = Field(default_factory=lambda: Money(amount=0))
    average_revenue_per_user: Money = Field(default_factory=lambda: Money(amount=0))
    
    # Conversion metrics
    trial_conversion_rate: float = 0.0
    churn_rate: float = 0.0
    retention_rate: float = 0.0
    
    # Distribution
    tier_distribution: Dict[str, int] = {}
    billing_interval_distribution: Dict[str, int] = {}
    
    # Growth metrics
    new_subscriptions_this_month: int = 0
    cancelled_subscriptions_this_month: int = 0
    net_new_subscribers: int = 0


# Webhook Models
class SubscriptionWebhook(BaseModel):
    """Subscription webhook event"""
    event_type: str
    subscription_id: str
    user_id: str
    event_data: Dict[str, Any]
    paystack_event_id: Optional[str] = None
    processed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Billing Information Models
class BillingInfo(BaseModel):
    """Billing information model"""
    user_id: str
    company_name: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: BillingAddress
    billing_email: EmailStr
    payment_methods: List[PaymentMethod] = []
    default_payment_method_id: Optional[str] = None
    auto_pay_enabled: bool = True
    invoice_delivery: str = "email"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Usage Tracking Models
class UsageEvent(BaseModel):
    """Individual usage event"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    subscription_id: str
    event_type: str
    quantity: int = 1
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    billing_period_start: datetime
    billing_period_end: datetime
    
    class Config:
        populate_by_name = True


class UsageSummary(BaseModel):
    """Usage summary for a billing period"""
    user_id: str
    subscription_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    usage_by_type: Dict[str, int] = {}
    total_usage: int = 0
    overage_charges: Money = Field(default_factory=lambda: Money(amount=0))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Customer Portal Models
class CustomerPortalSession(BaseModel):
    """Customer portal session"""
    user_id: str
    session_url: str
    return_url: str
    expires_at: datetime
    paystack_session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Subscription Change Models
class SubscriptionChange(BaseModel):
    """Subscription change request"""
    subscription_id: str
    user_id: str
    change_type: str
    from_plan_id: str
    to_plan_id: Optional[str] = None
    effective_date: Optional[datetime] = None
    proration: bool = True
    reason: Optional[str] = None
    requested_by: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


# Dunning Management Models
class DunningAttempt(BaseModel):
    """Dunning attempt for failed payment"""
    subscription_id: str
    user_id: str
    invoice_id: str
    attempt_number: int
    method: str
    status: str
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Referral and Affiliate Models
class ReferralProgram(BaseModel):
    """Referral program configuration"""
    id: str
    name: str
    description: str
    is_active: bool = True
    
    # Rewards
    referrer_reward_type: str = "credit"
    referrer_reward_amount: Money
    referee_reward_type: str = "discount"
    referee_reward_amount: Money
    
    # Conditions
    minimum_subscription_duration: int = 30
    maximum_rewards_per_user: Optional[int] = None
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    
    # Tracking
    total_referrals: int = 0
    successful_referrals: int = 0
    total_rewards_paid: Money = Field(default_factory=lambda: Money(amount=0))


class Referral(BaseModel):
    """Individual referral"""
    id: Optional[str] = Field(None, alias="_id")
    program_id: str = "default"
    referrer_user_id: str
    referee_email: str
    referee_user_id: Optional[str] = None
    referral_code: str
    
    # Status tracking
    status: str = "pending"
    referred_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Rewards
    referrer_reward_paid: bool = False
    referee_reward_paid: bool = False
    referrer_reward_amount: Optional[Money] = None
    referee_reward_amount: Optional[Money] = None
    
    # Metadata
    metadata: Dict[str, Any] = {}
    
    class Config:
        populate_by_name = True


# Tax and Compliance Models
class TaxRate(BaseModel):
    """Tax rate configuration"""
    jurisdiction: str
    tax_type: str
    rate: float
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None


class TaxCalculation(BaseModel):
    """Tax calculation for an invoice"""
    tax_rate: TaxRate
    taxable_amount: Money
    tax_amount: Money
    tax_inclusive: bool = False


# Subscription Events and Notifications
class SubscriptionEvent(BaseModel):
    """Subscription lifecycle event"""
    subscription_id: str
    user_id: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    notification_sent: bool = False


# Search and Filter Models
class SubscriptionFilter(BaseModel):
    """Subscription search filter"""
    status: Optional[List[SubscriptionStatus]] = None
    tier: Optional[List[SubscriptionTier]] = None
    billing_interval: Optional[List[BillingInterval]] = None
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    trial_ending_before: Optional[date] = None
    payment_failed: Optional[bool] = None
    cancel_at_period_end: Optional[bool] = None


class PaymentFilter(BaseModel):
    """Payment search filter"""
    status: Optional[List[PaymentStatus]] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    payment_method_type: Optional[List[PaymentMethodType]] = None


# Response Models for Lists
class SubscriptionListResponse(BaseModel):
    """Subscription list response"""
    subscriptions: List[SubscriptionResponse]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    stats: Optional[SubscriptionStats] = None


class PaymentListResponse(BaseModel):
    """Payment list response"""
    payments: List[Payment]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    total_amount: Money = Field(default_factory=lambda: Money(amount=0))


class InvoiceListResponse(BaseModel):
    """Invoice list response"""
    invoices: List[Invoice]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    total_amount_due: Money = Field(default_factory=lambda: Money(amount=0))


# Webhook and Integration Models
class PaystackWebhookEvent(BaseModel):
    """Paystack webhook event model"""
    id: str
    type: str
    data: Dict[str, Any]
    created: datetime
    livemode: bool
    pending_webhooks: int
    request_id: Optional[str] = None
    api_version: Optional[str] = None


# Credit and Balance Models
class AccountCredit(BaseModel):
    """Account credit/balance model"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    credit_type: str = "monetary"
    amount: Money
    description: str
    expires_at: Optional[datetime] = None
    is_used: bool = False
    used_at: Optional[datetime] = None
    source: str
    source_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class CreditTransaction(BaseModel):
    """Credit transaction model"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    credit_id: str
    transaction_type: str = "debit"
    amount: Money
    balance_before: Money
    balance_after: Money
    description: str
    related_invoice_id: Optional[str] = None
    related_subscription_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


# Export all subscription-related models
__all__ = [
    "SubscriptionStatus", "BillingInterval", "PaymentStatus", "PaymentMethodType",
    "InvoiceStatus", "RefundReason", "LimitType", "UsageLimit", "FeatureAccess", 
    "SubscriptionLimits", "SubscriptionPlan", "BillingAddress", "PaymentMethod", 
    "SubscriptionBase", "SubscriptionCreate", "SubscriptionUpdate", "Subscription", 
    "SubscriptionResponse", "InvoiceLineItem", "Invoice", "Payment", "Refund", 
    "PromoCode", "SubscriptionStats", "SubscriptionWebhook", "BillingInfo", 
    "UsageEvent", "UsageSummary", "CustomerPortalSession", "SubscriptionChange", 
    "DunningAttempt", "ReferralProgram", "Referral", "TaxRate", "TaxCalculation", 
    "SubscriptionEvent", "SubscriptionFilter", "PaymentFilter", "SubscriptionListResponse", 
    "PaymentListResponse", "InvoiceListResponse", "PaystackWebhookEvent", "AccountCredit", 
    "CreditTransaction"
]