# backend/app/schemas/__init__.py
"""
Database schemas package for MongoDB collections
"""

from .user import UserSchema, user_collection_schema
from .job import JobSchema, job_collection_schema
from .application import ApplicationSchema, application_collection_schema
from .subscription import SubscriptionSchema, subscription_collection_schema

# Collection schema registry
COLLECTION_SCHEMAS = {
    "users": user_collection_schema,
    "jobs": job_collection_schema,
    "applications": application_collection_schema,
    "subscriptions": subscription_collection_schema,
    "referrals": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["referrer_id", "referee_email", "referral_code", "status", "created_at"],
                "properties": {
                    "referrer_id": {"bsonType": "objectId"},
                    "referee_email": {"bsonType": "string"},
                    "referee_user_id": {"bsonType": ["objectId", "null"]},
                    "referral_code": {"bsonType": "string"},
                    "status": {
                        "bsonType": "string",
                        "enum": ["pending", "completed", "expired", "cancelled"]
                    },
                    "referred_at": {"bsonType": "date"},
                    "completed_at": {"bsonType": ["date", "null"]},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "documents": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "document_type", "filename", "file_path", "created_at"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "document_type": {
                        "bsonType": "string",
                        "enum": ["resume", "cv", "cover_letter", "portfolio", "certificate"]
                    },
                    "filename": {"bsonType": "string"},
                    "file_path": {"bsonType": "string"},
                    "file_size": {"bsonType": "long"},
                    "content_type": {"bsonType": "string"},
                    "version": {"bsonType": "int"},
                    "is_active": {"bsonType": "bool"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "usage_tracking": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "action", "timestamp"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "action": {"bsonType": "string"},
                    "timestamp": {"bsonType": "date"},
                    "metadata": {"bsonType": "object"},
                    "session_id": {"bsonType": ["string", "null"]},
                    "ip_address": {"bsonType": ["string", "null"]}
                }
            }
        }
    },
    "ml_training_data": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "data_type", "created_at"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "data_type": {
                        "bsonType": "string",
                        "enum": ["form_interaction", "job_preference", "application_outcome", "cv_performance"]
                    },
                    "data": {"bsonType": "object"},
                    "created_at": {"bsonType": "date"},
                    "processed": {"bsonType": "bool"}
                }
            }
        }
    }
}

# Index definitions
COLLECTION_INDEXES = {
    "users": [
        [("email", 1)],
        [("referral_code", 1)],
        [("created_at", -1)],
        [("subscription_tier", 1)],
        [("is_active", 1), ("is_verified", 1)]
    ],
    "jobs": [
        [("title", "text"), ("description", "text"), ("company_name", "text")],
        [("location", 1)],
        [("company_name", 1)],
        [("posted_date", -1)],
        [("source", 1)],
        [("status", 1)],
        [("employment_type", 1)],
        [("experience_level", 1)],
        [("created_at", -1)],
        [("relevance_score", -1)],
        [("skills_required", 1)],
        [("salary_range.min_amount", 1), ("salary_range.max_amount", 1)]
    ],
    "applications": [
        [("user_id", 1), ("applied_date", -1)],
        [("job_id", 1)],
        [("status", 1)],
        [("applied_date", -1)],
        [("user_id", 1), ("job_id", 1)],
        [("created_at", -1)],
        [("priority", 1)],
        [("company_name", 1)],
        [("next_follow_up", 1)]
    ],
    "subscriptions": [
        [("user_id", 1)],
        [("status", 1)],
        [("current_period_end", 1)],
        [("stripe_subscription_id", 1)],
        [("trial_end", 1)],
        [("next_billing_date", 1)]
    ],
    "referrals": [
        [("referrer_id", 1)],
        [("referee_email", 1)],
        [("referral_code", 1)],
        [("status", 1)],
        [("created_at", -1)]
    ],
    "documents": [
        [("user_id", 1), ("document_type", 1)],
        [("created_at", -1)],
        [("is_active", 1)]
    ],
    "usage_tracking": [
        [("user_id", 1), ("timestamp", -1)],
        [("action", 1)],
        [("timestamp", -1)]
    ],
    "ml_training_data": [
        [("user_id", 1)],
        [("data_type", 1)],
        [("created_at", -1)],
        [("processed", 1)]
    ]
}

__all__ = [
    "UserSchema",
    "JobSchema", 
    "ApplicationSchema",
    "SubscriptionSchema",
    "COLLECTION_SCHEMAS",
    "COLLECTION_INDEXES",
    "user_collection_schema",
    "job_collection_schema",
    "application_collection_schema",
    "subscription_collection_schema"
]