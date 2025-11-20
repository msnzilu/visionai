# backend/app/schemas/subscription.py
"""
Subscription collection database schema for MongoDB
"""

from typing import Dict, Any, List
from pymongo import IndexModel, ASCENDING, DESCENDING


class SubscriptionSchema:
    """Subscription collection schema definitions"""
    
    # Collection name
    COLLECTION_NAME = "subscriptions"
    
    # MongoDB JSON Schema validator
    @staticmethod
    def get_validator() -> Dict[str, Any]:
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "user_id", "plan_id", "status", "billing_interval",
                    "current_period_start", "current_period_end", "created_at", "updated_at"
                ],
                "properties": {
                    "user_id": {
                        "bsonType": "objectId",
                        "description": "Reference to user document"
                    },
                    "plan_id": {
                        "bsonType": "string",
                        "description": "Subscription plan identifier"
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": [
                            "active", "inactive", "pending", "cancelled", "suspended",
                            "expired", "past_due", "trialing", "incomplete", 
                            "incomplete_expired", "unpaid"
                        ],
                        "description": "Current subscription status"
                    },
                    "billing_interval": {
                        "bsonType": "string",
                        "enum": ["monthly", "yearly", "weekly", "daily"],
                        "description": "Billing frequency"
                    },
                    "payment_method_id": {
                        "bsonType": ["string", "null"],
                        "description": "Reference to payment method"
                    },
                    "plan": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "id": {"bsonType": "string"},
                            "name": {"bsonType": "string"},
                            "tier": {
                                "bsonType": "string",
                                "enum": ["free", "basic", "premium"]
                            },
                            "description": {"bsonType": "string"},
                            "price": {
                                "bsonType": "object",
                                "required": ["amount", "currency"],
                                "properties": {
                                    "amount": {
                                        "bsonType": "double",
                                        "minimum": 0
                                    },
                                    "currency": {
                                        "bsonType": "string",
                                        "enum": ["USD", "EUR", "GBP", "CAD", "AUD"]
                                    }
                                }
                            },
                            "trial_period_days": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "limits": {
                                "bsonType": "object",
                                "properties": {
                                    "monthly_job_searches": {
                                        "bsonType": "object",
                                        "properties": {
                                            "name": {"bsonType": "string"},
                                            "limit_type": {"bsonType": "string"},
                                            "max_value": {"bsonType": "int"},
                                            "current_value": {"bsonType": "int"},
                                            "is_hard_limit": {"bsonType": "bool"}
                                        }
                                    },
                                    "jobs_per_search": {
                                        "bsonType": "object",
                                        "properties": {
                                            "max_value": {"bsonType": "int"},
                                            "current_value": {"bsonType": "int"}
                                        }
                                    }
                                }
                            },
                            "features": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            },
                            "stripe_price_id": {"bsonType": ["string", "null"]},
                            "stripe_product_id": {"bsonType": ["string", "null"]}
                        }
                    },
                    "current_period_start": {
                        "bsonType": "date",
                        "description": "Current billing period start"
                    },
                    "current_period_end": {
                        "bsonType": "date",
                        "description": "Current billing period end"
                    },
                    "trial_start": {
                        "bsonType": ["date", "null"],
                        "description": "Trial period start date"
                    },
                    "trial_end": {
                        "bsonType": ["date", "null"],
                        "description": "Trial period end date"
                    },
                    "cancel_at_period_end": {
                        "bsonType": "bool",
                        "default": False,
                        "description": "Whether to cancel at period end"
                    },
                    "cancelled_at": {
                        "bsonType": ["date", "null"],
                        "description": "Cancellation timestamp"
                    },
                    "cancellation_reason": {
                        "bsonType": ["string", "null"],
                        "maxLength": 500,
                        "description": "Reason for cancellation"
                    },
                    "current_usage": {
                        "bsonType": "object",
                        "properties": {
                            "monthly_searches": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "daily_searches": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "cv_customizations": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "cover_letter_generations": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "auto_applications": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "last_reset": {
                                "bsonType": "date",
                                "description": "Last usage reset timestamp"
                            }
                        }
                    },
                    "usage_reset_date": {
                        "bsonType": ["date", "null"],
                        "description": "Next usage reset date"
                    },
                    "stripe_subscription_id": {
                        "bsonType": ["string", "null"],
                        "description": "Stripe subscription ID"
                    },
                    "stripe_customer_id": {
                        "bsonType": ["string", "null"],
                        "description": "Stripe customer ID"
                    },
                    "next_billing_date": {
                        "bsonType": ["date", "null"],
                        "description": "Next billing date"
                    },
                    "last_payment_date": {
                        "bsonType": ["date", "null"],
                        "description": "Last successful payment date"
                    },
                    "payment_failed_count": {
                        "bsonType": "int",
                        "minimum": 0,
                        "default": 0,
                        "description": "Number of consecutive payment failures"
                    },
                    "metadata": {
                        "bsonType": "object",
                        "description": "Additional metadata"
                    },
                    "notes": {
                        "bsonType": ["string", "null"],
                        "maxLength": 1000,
                        "description": "Admin notes"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Subscription creation timestamp"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Last update timestamp"
                    }
                }
            }
        }
    
    # Index definitions
    @staticmethod
    def get_indexes() -> List[IndexModel]:
        return [
            # Primary indexes
            IndexModel([("user_id", ASCENDING)], unique=True, name="user_id_unique"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("plan_id", ASCENDING)], name="plan_id_idx"),
            IndexModel([("billing_interval", ASCENDING)], name="billing_interval_idx"),
            
            # Date-based indexes
            IndexModel([("current_period_end", ASCENDING)], name="current_period_end_idx"),
            IndexModel([("trial_end", ASCENDING)], name="trial_end_idx"),
            IndexModel([("next_billing_date", ASCENDING)], name="next_billing_date_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_desc_idx"),
            IndexModel([("cancelled_at", DESCENDING)], name="cancelled_at_desc_idx"),
            
            # Stripe integration
            IndexModel([("stripe_subscription_id", ASCENDING)], name="stripe_subscription_id_idx"),
            IndexModel([("stripe_customer_id", ASCENDING)], name="stripe_customer_id_idx"),
            
            # Payment tracking
            IndexModel([("payment_failed_count", DESCENDING)], name="payment_failed_count_desc_idx"),
            IndexModel([("last_payment_date", DESCENDING)], name="last_payment_date_desc_idx"),
            
            # Usage tracking
            IndexModel([("usage_reset_date", ASCENDING)], name="usage_reset_date_idx"),
            IndexModel([("current_usage.monthly_searches", DESCENDING)], name="monthly_searches_desc_idx"),
            
            # Plan and tier analysis
            IndexModel([("plan.tier", ASCENDING)], name="plan_tier_idx"),
            IndexModel([("plan.price.amount", DESCENDING)], name="plan_price_desc_idx"),
            
            # Cancellation tracking
            IndexModel([("cancel_at_period_end", ASCENDING)], name="cancel_at_period_end_idx"),
            IndexModel([("cancellation_reason", ASCENDING)], name="cancellation_reason_idx"),
            
            # Compound indexes for complex queries
            IndexModel([
                ("status", ASCENDING),
                ("current_period_end", ASCENDING)
            ], name="status_period_end_idx"),
            
            IndexModel([
                ("plan.tier", ASCENDING),
                ("status", ASCENDING),
                ("created_at", DESCENDING)
            ], name="tier_status_created_idx"),
            
            IndexModel([
                ("trial_end", ASCENDING),
                ("status", ASCENDING)
            ], name="trial_end_status_idx"),
            
            IndexModel([
                ("payment_failed_count", ASCENDING),
                ("next_billing_date", ASCENDING)
            ], name="payment_failed_billing_idx")
        ]
    
    # Default values for new documents
    @staticmethod
    def get_defaults() -> Dict[str, Any]:
        from datetime import datetime, timedelta
        
        return {
            "status": "active",
            "billing_interval": "monthly",
            "cancel_at_period_end": False,
            "payment_failed_count": 0,
            "current_usage": {
                "monthly_searches": 0,
                "daily_searches": 0,
                "cv_customizations": 0,
                "cover_letter_generations": 0,
                "auto_applications": 0,
                "last_reset": datetime.utcnow()
            },
            "metadata": {}
        }
    
    # Aggregation pipelines
    @staticmethod
    def get_subscription_stats_pipeline() -> List[Dict[str, Any]]:
        """Aggregation pipeline for subscription statistics"""
        return [
            {
                "$group": {
                    "_id": None,
                    "total_subscriptions": {"$sum": 1},
                    "active_subscriptions": {
                        "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                    },
                    "trial_subscriptions": {
                        "$sum": {"$cond": [{"$eq": ["$status", "trialing"]}, 1, 0]}
                    },
                    "cancelled_subscriptions": {
                        "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                    },
                    "total_mrr": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", "active"]},
                                {
                                    "$cond": [
                                        {"$eq": ["$billing_interval", "monthly"]},
                                        "$plan.price.amount",
                                        {"$divide": ["$plan.price.amount", 12]}
                                    ]
                                },
                                0
                            ]
                        }
                    },
                    "avg_plan_value": {"$avg": "$plan.price.amount"},
                    "tier_distribution": {
                        "$push": "$plan.tier"
                    },
                    "billing_distribution": {
                        "$push": "$billing_interval"
                    }
                }
            },
            {
                "$addFields": {
                    "arr": {"$multiply": ["$total_mrr", 12]},
                    "tier_counts": {
                        "$arrayToObject": {
                            "$map": {
                                "input": ["free", "basic", "premium"],
                                "as": "tier",
                                "in": {
                                    "k": "$$tier",
                                    "v": {
                                        "$size": {
                                            "$filter": {
                                                "input": "$tier_distribution",
                                                "cond": {"$eq": ["$$this", "$$tier"]}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "billing_counts": {
                        "$arrayToObject": {
                            "$map": {
                                "input": ["monthly", "yearly"],
                                "as": "interval",
                                "in": {
                                    "k": "$$interval",
                                    "v": {
                                        "$size": {
                                            "$filter": {
                                                "input": "$billing_distribution",
                                                "cond": {"$eq": ["$$this", "$$interval"]}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
    
    @staticmethod
    def get_churn_analysis_pipeline(days: int = 30) -> List[Dict[str, Any]]:
        """Aggregation pipeline for churn analysis"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return [
            {
                "$facet": {
                    "cancelled_recently": [
                        {
                            "$match": {
                                "status": "cancelled",
                                "cancelled_at": {"$gte": cutoff_date}
                            }
                        },
                        {
                            "$group": {
                                "_id": "$plan.tier",
                                "count": {"$sum": 1},
                                "reasons": {"$push": "$cancellation_reason"},
                                "avg_lifetime_days": {
                                    "$avg": {
                                        "$divide": [
                                            {"$subtract": ["$cancelled_at", "$created_at"]},
                                            86400000
                                        ]
                                    }
                                }
                            }
                        }
                    ],
                    "trial_conversions": [
                        {
                            "$match": {
                                "trial_end": {"$gte": cutoff_date, "$lte": datetime.utcnow()}
                            }
                        },
                        {
                            "$group": {
                                "_id": "$status",
                                "count": {"$sum": 1}
                            }
                        }
                    ],
                    "payment_failures": [
                        {
                            "$match": {
                                "payment_failed_count": {"$gt": 0}
                            }
                        },
                        {
                            "$group": {
                                "_id": "$payment_failed_count",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"_id": 1}}
                    ]
                }
            }
        ]
    
    @staticmethod
    def get_usage_analytics_pipeline(user_id: str = None) -> List[Dict[str, Any]]:
        """Aggregation pipeline for usage analytics"""
        match_stage = {"$match": {"user_id": user_id}} if user_id else {"$match": {"status": "active"}}
        
        return [
            match_stage,
            {
                "$group": {
                    "_id": "$plan.tier",
                    "user_count": {"$sum": 1},
                    "avg_monthly_searches": {"$avg": "$current_usage.monthly_searches"},
                    "avg_cv_customizations": {"$avg": "$current_usage.cv_customizations"},
                    "avg_cover_letters": {"$avg": "$current_usage.cover_letter_generations"},
                    "avg_auto_applications": {"$avg": "$current_usage.auto_applications"},
                    "total_searches": {"$sum": "$current_usage.monthly_searches"},
                    "max_searches": {"$max": "$current_usage.monthly_searches"}
                }
            },
            {
                "$addFields": {
                    "utilization_rate": {
                        "$cond": [
                            {"$eq": ["$_id", "free"]},
                            {"$divide": ["$avg_monthly_searches", 1]},
                            {
                                "$cond": [
                                    {"$eq": ["$_id", "basic"]},
                                    {"$divide": ["$avg_monthly_searches", 150]},
                                    {"$divide": ["$avg_monthly_searches", 200]}
                                ]
                            }
                        ]
                    }
                }
            },
            {"$sort": {"_id": 1}}
        ]
    
    @staticmethod
    def get_billing_issues_pipeline() -> List[Dict[str, Any]]:
        """Aggregation pipeline for billing issues"""
        from datetime import datetime, timedelta
        
        return [
            {
                "$match": {
                    "$or": [
                        {"payment_failed_count": {"$gt": 0}},
                        {"status": "past_due"},
                        {"next_billing_date": {"$lt": datetime.utcnow()}}
                    ]
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": "$user_info"},
            {
                "$project": {
                    "user_id": 1,
                    "user_email": "$user_info.email",
                    "user_name": {
                        "$concat": ["$user_info.first_name", " ", "$user_info.last_name"]
                    },
                    "status": 1,
                    "payment_failed_count": 1,
                    "next_billing_date": 1,
                    "last_payment_date": 1,
                    "plan_name": "$plan.name",
                    "plan_amount": "$plan.price.amount",
                    "days_overdue": {
                        "$cond": [
                            {"$lt": ["$next_billing_date", datetime.utcnow()]},
                            {
                                "$divide": [
                                    {"$subtract": [datetime.utcnow(), "$next_billing_date"]},
                                    86400000
                                ]
                            },
                            0
                        ]
                    }
                }
            },
            {"$sort": {"payment_failed_count": -1, "days_overdue": -1}}
        ]
    
    @staticmethod
    def get_revenue_pipeline(months: int = 12) -> List[Dict[str, Any]]:
        """Aggregation pipeline for revenue analysis"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=months * 30)
        
        return [
            {
                "$match": {
                    "status": {"$in": ["active", "cancelled"]},
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "tier": "$plan.tier"
                    },
                    "new_subscriptions": {"$sum": 1},
                    "revenue": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$billing_interval", "monthly"]},
                                "$plan.price.amount",
                                {"$divide": ["$plan.price.amount", 12]}
                            ]
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": "$_id.year",
                        "month": "$_id.month"
                    },
                    "total_new_subscriptions": {"$sum": "$new_subscriptions"},
                    "total_revenue": {"$sum": "$revenue"},
                    "tier_breakdown": {
                        "$push": {
                            "tier": "$_id.tier",
                            "subscriptions": "$new_subscriptions",
                            "revenue": "$revenue"
                        }
                    }
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
    
    @staticmethod
    def get_expiring_trials_pipeline(days: int = 7) -> List[Dict[str, Any]]:
        """Aggregation pipeline for trials expiring soon"""
        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow() + timedelta(days=days)
        
        return [
            {
                "$match": {
                    "status": "trialing",
                    "trial_end": {
                        "$gte": datetime.utcnow(),
                        "$lte": end_date
                    }
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": "$user_info"},
            {
                "$project": {
                    "user_id": 1,
                    "user_email": "$user_info.email",
                    "user_name": {
                        "$concat": ["$user_info.first_name", " ", "$user_info.last_name"]
                    },
                    "trial_end": 1,
                    "plan_name": "$plan.name",
                    "plan_amount": "$plan.price.amount",
                    "usage": "$current_usage",
                    "days_remaining": {
                        "$divide": [
                            {"$subtract": ["$trial_end", datetime.utcnow()]},
                            86400000
                        ]
                    }
                }
            },
            {"$sort": {"trial_end": 1}}
        ]


# Payment method schema
class PaymentMethodSchema:
    """Payment method collection schema"""
    
    COLLECTION_NAME = "payment_methods"
    
    @staticmethod
    def get_validator() -> Dict[str, Any]:
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "type", "created_at"],
                "properties": {
                    "user_id": {
                        "bsonType": "objectId",
                        "description": "Reference to user document"
                    },
                    "type": {
                        "bsonType": "string",
                        "enum": ["card", "bank_account", "paypal", "apple_pay", "google_pay", "stripe"]
                    },
                    "is_default": {
                        "bsonType": "bool",
                        "default": False
                    },
                    "card_brand": {"bsonType": ["string", "null"]},
                    "card_last_four": {"bsonType": ["string", "null"]},
                    "card_exp_month": {
                        "bsonType": ["int", "null"],
                        "minimum": 1,
                        "maximum": 12
                    },
                    "card_exp_year": {
                        "bsonType": ["int", "null"],
                        "minimum": 2024
                    },
                    "billing_address": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "line1": {"bsonType": "string"},
                            "line2": {"bsonType": ["string", "null"]},
                            "city": {"bsonType": "string"},
                            "state": {"bsonType": ["string", "null"]},
                            "postal_code": {"bsonType": "string"},
                            "country": {"bsonType": "string"}
                        }
                    },
                    "stripe_payment_method_id": {"bsonType": ["string", "null"]},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    
    @staticmethod
    def get_indexes() -> List[IndexModel]:
        return [
            IndexModel([("user_id", ASCENDING)], name="user_id_idx"),
            IndexModel([("type", ASCENDING)], name="type_idx"),
            IndexModel([("is_default", ASCENDING)], name="is_default_idx"),
            IndexModel([("stripe_payment_method_id", ASCENDING)], name="stripe_payment_method_id_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_desc_idx")
        ]


# Invoice schema
class InvoiceSchema:
    """Invoice collection schema"""
    
    COLLECTION_NAME = "invoices"
    
    @staticmethod
    def get_validator() -> Dict[str, Any]:
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "invoice_number", "status", "total_amount", "invoice_date"],
                "properties": {
                    "user_id": {
                        "bsonType": "objectId",
                        "description": "Reference to user document"
                    },
                    "subscription_id": {
                        "bsonType": ["objectId", "null"],
                        "description": "Reference to subscription document"
                    },
                    "invoice_number": {
                        "bsonType": "string",
                        "description": "Unique invoice number"
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": ["draft", "open", "paid", "void", "uncollectible"]
                    },
                    "subtotal": {
                        "bsonType": "object",
                        "required": ["amount", "currency"],
                        "properties": {
                            "amount": {"bsonType": "double"},
                            "currency": {"bsonType": "string"}
                        }
                    },
                    "tax_amount": {
                        "bsonType": "object",
                        "properties": {
                            "amount": {"bsonType": "double"},
                            "currency": {"bsonType": "string"}
                        }
                    },
                    "total_amount": {
                        "bsonType": "object",
                        "required": ["amount", "currency"],
                        "properties": {
                            "amount": {"bsonType": "double"},
                            "currency": {"bsonType": "string"}
                        }
                    },
                    "amount_paid": {
                        "bsonType": "object",
                        "properties": {
                            "amount": {"bsonType": "double"},
                            "currency": {"bsonType": "string"}
                        }
                    },
                    "line_items": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["description", "unit_amount", "total_amount"],
                            "properties": {
                                "description": {"bsonType": "string"},
                                "quantity": {"bsonType": "int"},
                                "unit_amount": {
                                    "bsonType": "object",
                                    "properties": {
                                        "amount": {"bsonType": "double"},
                                        "currency": {"bsonType": "string"}
                                    }
                                },
                                "total_amount": {
                                    "bsonType": "object",
                                    "properties": {
                                        "amount": {"bsonType": "double"},
                                        "currency": {"bsonType": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "invoice_date": {"bsonType": "date"},
                    "due_date": {"bsonType": ["date", "null"]},
                    "paid_date": {"bsonType": ["date", "null"]},
                    "stripe_invoice_id": {"bsonType": ["string", "null"]},
                    "created_at": {"bsonType": "date"}
                }
            }
        }
    
    @staticmethod
    def get_indexes() -> List[IndexModel]:
        return [
            IndexModel([("user_id", ASCENDING)], name="user_id_idx"),
            IndexModel([("subscription_id", ASCENDING)], name="subscription_id_idx"),
            IndexModel([("invoice_number", ASCENDING)], unique=True, name="invoice_number_unique"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("invoice_date", DESCENDING)], name="invoice_date_desc_idx"),
            IndexModel([("due_date", ASCENDING)], name="due_date_asc_idx"),
            IndexModel([("stripe_invoice_id", ASCENDING)], name="stripe_invoice_id_idx")
        ]


# Collection schemas for MongoDB validation
subscription_collection_schema = {
    "validator": SubscriptionSchema.get_validator(),
    "validationLevel": "strict",
    "validationAction": "error"
}

payment_method_collection_schema = {
    "validator": PaymentMethodSchema.get_validator(),
    "validationLevel": "strict",
    "validationAction": "error"
}

invoice_collection_schema = {
    "validator": InvoiceSchema.get_validator(),
    "validationLevel": "strict", 
    "validationAction": "error"
}

# Export schema classes and collection schemas
__all__ = [
    "SubscriptionSchema", 
    "PaymentMethodSchema", 
    "InvoiceSchema",
    "subscription_collection_schema",
    "payment_method_collection_schema", 
    "invoice_collection_schema"
]