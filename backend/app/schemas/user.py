# backend/app/schemas/user.py
"""
User collection database schema for MongoDB
"""

from typing import Dict, Any, List
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT


class UserSchema:
    """User collection schema definitions"""
    
    # Collection name
    COLLECTION_NAME = "users"
    
    # MongoDB JSON Schema validator
    @staticmethod
    def get_validator() -> Dict[str, Any]:
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "email", "password", "first_name", "last_name", 
                    "is_active", "is_verified", "role", "subscription_tier",
                    "referral_code", "created_at", "updated_at"
                ],
                "properties": {
                    "email": {
                        "bsonType": "string",
                        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                        "description": "Valid email address"
                    },
                    "password": {
                        "bsonType": "string",
                        "minLength": 8,
                        "description": "Hashed password"
                    },
                    "first_name": {
                        "bsonType": "string",
                        "minLength": 1,
                        "maxLength": 50
                    },
                    "last_name": {
                        "bsonType": "string",
                        "minLength": 1,
                        "maxLength": 50
                    },
                    "phone": {
                        "bsonType": ["string", "null"],
                        "pattern": "^\\+?[\\d\\s\\-\\(\\)]{7,15}$"
                    },
                    "is_active": {
                        "bsonType": "bool",
                        "description": "Whether user account is active"
                    },
                    "is_verified": {
                        "bsonType": "bool",
                        "description": "Whether email is verified"
                    },
                    "role": {
                        "bsonType": "string",
                        "enum": ["user", "admin", "moderator"],
                        "description": "User role"
                    },
                    "subscription_tier": {
                        "bsonType": "string",
                        "enum": ["free", "basic", "premium"],
                        "description": "Subscription tier"
                    },
                    "profile": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "personal_info": {
                                "bsonType": ["object", "null"],
                                "properties": {
                                    "address": {"bsonType": ["string", "null"]},
                                    "city": {"bsonType": ["string", "null"]},
                                    "state": {"bsonType": ["string", "null"]},
                                    "country": {"bsonType": ["string", "null"]},
                                    "postal_code": {"bsonType": ["string", "null"]},
                                    "linkedin_url": {"bsonType": ["string", "null"]},
                                    "portfolio_url": {"bsonType": ["string", "null"]},
                                    "github_url": {"bsonType": ["string", "null"]}
                                }
                            },
                            "location_preferences": {
                                "bsonType": ["object", "null"],
                                "properties": {
                                    "city": {"bsonType": ["string", "null"]},
                                    "state": {"bsonType": ["string", "null"]},
                                    "country": {"bsonType": "string"},
                                    "remote_ok": {"bsonType": "bool"},
                                    "radius_miles": {
                                        "bsonType": "int",
                                        "minimum": 1,
                                        "maximum": 500
                                    },
                                    "coordinates": {
                                        "bsonType": ["object", "null"],
                                        "properties": {
                                            "lat": {
                                                "bsonType": "double",
                                                "minimum": -90,
                                                "maximum": 90
                                            },
                                            "lng": {
                                                "bsonType": "double",
                                                "minimum": -180,
                                                "maximum": 180
                                            }
                                        }
                                    }
                                }
                            },
                            "job_preferences": {
                                "bsonType": ["object", "null"],
                                "properties": {
                                    "job_titles": {
                                        "bsonType": "array",
                                        "items": {"bsonType": "string"}
                                    },
                                    "industries": {
                                        "bsonType": "array",
                                        "items": {"bsonType": "string"}
                                    },
                                    "company_sizes": {
                                        "bsonType": "array",
                                        "items": {
                                            "bsonType": "string",
                                            "enum": ["startup", "small", "medium", "large", "enterprise"]
                                        }
                                    },
                                    "employment_types": {
                                        "bsonType": "array",
                                        "items": {
                                            "bsonType": "string",
                                            "enum": ["full_time", "part_time", "contract", "internship"]
                                        }
                                    },
                                    "experience_levels": {
                                        "bsonType": "array",
                                        "items": {
                                            "bsonType": "string",
                                            "enum": ["entry_level", "junior", "mid_level", "senior", "lead", "executive"]
                                        }
                                    },
                                    "salary_min": {
                                        "bsonType": ["int", "null"],
                                        "minimum": 0
                                    },
                                    "salary_max": {
                                        "bsonType": ["int", "null"],
                                        "minimum": 0
                                    },
                                    "salary_currency": {
                                        "bsonType": "string",
                                        "enum": ["USD", "EUR", "GBP", "CAD", "AUD"]
                                    },
                                    "work_arrangements": {
                                        "bsonType": "array",
                                        "items": {
                                            "bsonType": "string",
                                            "enum": ["remote", "hybrid", "on_site"]
                                        }
                                    }
                                }
                            },
                            "bio": {
                                "bsonType": ["string", "null"],
                                "maxLength": 1000
                            },
                            "skills": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            },
                            "experience_years": {
                                "bsonType": "int",
                                "minimum": 0,
                                "maximum": 50
                            },
                            "education_level": {
                                "bsonType": ["string", "null"],
                                "enum": ["high_school", "bachelor", "master", "phd"]
                            },
                            "availability": {
                                "bsonType": ["string", "null"],
                                "enum": ["immediate", "2_weeks", "1_month", "3_months"]
                            },
                            "cover_letter_tone": {
                                "bsonType": "string",
                                "enum": ["professional", "casual", "creative"],
                                "default": "professional"
                            },
                            "timezone": {"bsonType": ["string", "null"]}
                        }
                    },
                    "usage_stats": {
                        "bsonType": "object",
                        "properties": {
                            "total_searches": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "total_applications": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "successful_applications": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "cv_customizations": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "cover_letters_generated": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "monthly_searches": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "daily_searches": {
                                "bsonType": "int",
                                "minimum": 0
                            },
                            "success_rate": {
                                "bsonType": "double",
                                "minimum": 0,
                                "maximum": 1
                            },
                            "avg_applications_per_search": {
                                "bsonType": "double",
                                "minimum": 0
                            }
                        }
                    },
                    "preferences": {
                        "bsonType": "object",
                        "properties": {
                            "email_notifications": {"bsonType": "bool"},
                            "sms_notifications": {"bsonType": "bool"},
                            "push_notifications": {"bsonType": "bool"},
                            "marketing_emails": {"bsonType": "bool"},
                            "application_reminders": {"bsonType": "bool"},
                            "job_alerts": {"bsonType": "bool"},
                            "weekly_reports": {"bsonType": "bool"},
                            "language": {
                                "bsonType": "string",
                                "enum": ["en", "es", "fr", "de", "pt", "it"]
                            },
                            "theme": {
                                "bsonType": "string",
                                "enum": ["light", "dark"]
                            },
                            "dashboard_layout": {"bsonType": "string"}
                        }
                    },
                    "referral_code": {
                        "bsonType": "string",
                        "minLength": 6,
                        "maxLength": 12,
                        "description": "Unique referral code"
                    },
                    "referred_by": {
                        "bsonType": ["objectId", "null"],
                        "description": "ID of user who referred this user"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Account creation timestamp"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Last update timestamp"
                    },
                    "last_login": {
                        "bsonType": ["date", "null"],
                        "description": "Last login timestamp"
                    },
                    "verified_at": {
                        "bsonType": ["date", "null"],
                        "description": "Email verification timestamp"
                    },
                    "cv_uploaded_at": {
                        "bsonType": ["date", "null"],
                        "description": "CV upload timestamp"
                    },
                    "terms_accepted": {
                        "bsonType": "bool",
                        "description": "Whether user accepted terms"
                    },
                    "newsletter_subscription": {
                        "bsonType": "bool",
                        "description": "Newsletter subscription preference"
                    }
                }
            }
        }
    
    # Index definitions
    @staticmethod
    def get_indexes() -> List[IndexModel]:
        return [
            # Unique indexes
            IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
            IndexModel([("referral_code", ASCENDING)], unique=True, name="referral_code_unique"),
            
            # Query optimization indexes
            IndexModel([("subscription_tier", ASCENDING)], name="subscription_tier_idx"),
            IndexModel([("is_active", ASCENDING), ("is_verified", ASCENDING)], name="user_status_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_desc_idx"),
            IndexModel([("last_login", DESCENDING)], name="last_login_desc_idx"),
            
            # Location-based queries
            IndexModel([("profile.location_preferences.country", ASCENDING)], name="country_idx"),
            IndexModel([("profile.location_preferences.city", ASCENDING)], name="city_idx"),
            IndexModel([("profile.location_preferences.coordinates", "2dsphere")], name="location_geo_idx"),
            
            # Skills and preferences
            IndexModel([("profile.skills", ASCENDING)], name="skills_idx"),
            IndexModel([("profile.job_preferences.industries", ASCENDING)], name="industries_idx"),
            IndexModel([("profile.job_preferences.job_titles", ASCENDING)], name="job_titles_idx"),
            
            # Usage statistics
            IndexModel([("usage_stats.total_searches", DESCENDING)], name="total_searches_desc_idx"),
            IndexModel([("usage_stats.success_rate", DESCENDING)], name="success_rate_desc_idx"),
            
            # Admin queries
            IndexModel([("role", ASCENDING)], name="role_idx"),
            IndexModel([("referred_by", ASCENDING)], name="referred_by_idx"),
            
            # Compound indexes for complex queries
            IndexModel([
                ("subscription_tier", ASCENDING), 
                ("is_active", ASCENDING), 
                ("created_at", DESCENDING)
            ], name="subscription_active_created_idx"),
            
            IndexModel([
                ("profile.location_preferences.country", ASCENDING),
                ("profile.job_preferences.industries", ASCENDING)
            ], name="location_industry_idx")
        ]
    
    # Default values for new documents
    @staticmethod
    def get_defaults() -> Dict[str, Any]:
        return {
            "is_active": True,
            "is_verified": False,
            "role": "user",
            "subscription_tier": "free",
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
            "terms_accepted": True,
            "newsletter_subscription": False
        }
    
    # Validation rules for updates
    @staticmethod
    def get_update_validation() -> Dict[str, Any]:
        """Validation rules for update operations"""
        return {
            "email": {
                "immutable": True,  # Email cannot be changed after creation
                "validation": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            },
            "referral_code": {
                "immutable": True  # Referral code cannot be changed
            },
            "subscription_tier": {
                "allowed_values": ["free", "basic", "premium"]
            },
            "role": {
                "admin_only": True,  # Only admins can change roles
                "allowed_values": ["user", "admin", "moderator"]
            }
        }
    
    # Aggregation pipelines
    @staticmethod
    def get_user_stats_pipeline(user_id: str = None) -> List[Dict[str, Any]]:
        """Aggregation pipeline for user statistics"""
        match_stage = {"$match": {"_id": user_id}} if user_id else {"$match": {}}
        
        return [
            match_stage,
            {
                "$group": {
                    "_id": "$subscription_tier",
                    "count": {"$sum": 1},
                    "avg_searches": {"$avg": "$usage_stats.total_searches"},
                    "avg_success_rate": {"$avg": "$usage_stats.success_rate"},
                    "total_applications": {"$sum": "$usage_stats.total_applications"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
    
    @staticmethod
    def get_referral_stats_pipeline(referrer_id: str) -> List[Dict[str, Any]]:
        """Aggregation pipeline for referral statistics"""
        return [
            {
                "$match": {"referred_by": referrer_id}
            },
            {
                "$group": {
                    "_id": None,
                    "total_referrals": {"$sum": 1},
                    "active_referrals": {
                        "$sum": {
                            "$cond": [{"$eq": ["$is_active", True]}, 1, 0]
                        }
                    },
                    "verified_referrals": {
                        "$sum": {
                            "$cond": [{"$eq": ["$is_verified", True]}, 1, 0]
                        }
                    },
                    "premium_referrals": {
                        "$sum": {
                            "$cond": [{"$ne": ["$subscription_tier", "free"]}, 1, 0]
                        }
                    }
                }
            }
        ]


# Collection schema for MongoDB validation
user_collection_schema = {
    "validator": UserSchema.get_validator(),
    "validationLevel": "strict",
    "validationAction": "error"
}

# Export schema class and collection schema
__all__ = ["UserSchema", "user_collection_schema"]