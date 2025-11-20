# backend/app/schemas/job.py
"""
Job collection database schema for MongoDB
"""

from typing import Dict, Any, List
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT


class JobSchema:
    """Job collection schema definitions"""
    
    # Collection name
    COLLECTION_NAME = "jobs"
    
    # MongoDB JSON Schema validator
    @staticmethod
    def get_validator() -> Dict[str, Any]:
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "title", "description", "company_name", "location", 
                    "status", "source", "created_at", "updated_at"
                ],
                "properties": {
                    "title": {
                        "bsonType": "string",
                        "minLength": 1,
                        "maxLength": 200,
                        "description": "Job title"
                    },
                    "description": {
                        "bsonType": "string",
                        "minLength": 10,
                        "description": "Job description"
                    },
                    "company_name": {
                        "bsonType": "string",
                        "minLength": 1,
                        "maxLength": 100,
                        "description": "Company name"
                    },
                    "location": {
                        "bsonType": "string",
                        "minLength": 1,
                        "maxLength": 200,
                        "description": "Job location"
                    },
                    "employment_type": {
                        "bsonType": ["string", "null"],
                        "enum": ["full_time", "part_time", "contract", "temporary", "internship", "freelance", "volunteer"]
                    },
                    "work_arrangement": {
                        "bsonType": ["string", "null"],
                        "enum": ["on_site", "remote", "hybrid", "flexible"]
                    },
                    "experience_level": {
                        "bsonType": ["string", "null"],
                        "enum": ["entry_level", "junior", "mid_level", "senior", "lead", "principal", "director", "executive"]
                    },
                    "salary_range": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "min_amount": {
                                "bsonType": ["double", "null"],
                                "minimum": 0
                            },
                            "max_amount": {
                                "bsonType": ["double", "null"],
                                "minimum": 0
                            },
                            "currency": {
                                "bsonType": "string",
                                "enum": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
                            },
                            "period": {
                                "bsonType": "string",
                                "enum": ["yearly", "monthly", "weekly", "hourly"]
                            },
                            "is_negotiable": {"bsonType": "bool"}
                        }
                    },
                    "requirements": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["requirement"],
                            "properties": {
                                "requirement": {"bsonType": "string"},
                                "is_required": {"bsonType": "bool"},
                                "category": {"bsonType": "string"},
                                "priority": {
                                    "bsonType": "string",
                                    "enum": ["low", "medium", "high", "urgent"]
                                }
                            }
                        }
                    },
                    "benefits": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"bsonType": "string"},
                                "description": {"bsonType": ["string", "null"]},
                                "category": {"bsonType": "string"},
                                "value": {"bsonType": ["string", "null"]}
                            }
                        }
                    },
                    "skills_required": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "skills_preferred": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"}
                    },
                    "application_deadline": {
                        "bsonType": ["date", "null"]
                    },
                    "start_date": {
                        "bsonType": ["date", "null"]
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": ["active", "inactive", "filled", "expired", "draft", "pending"]
                    },
                    "source": {
                        "bsonType": "string",
                        "enum": ["indeed", "linkedin", "glassdoor", "company_website", "job_board", "manual", "api", "scraper"]
                    },
                    "external_id": {
                        "bsonType": ["string", "null"],
                        "description": "External job ID from source"
                    },
                    "external_url": {
                        "bsonType": ["string", "null"],
                        "description": "External job URL"
                    },
                    "company_info": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "name": {"bsonType": "string"},
                            "description": {"bsonType": ["string", "null"]},
                            "website": {"bsonType": ["string", "null"]},
                            "logo_url": {"bsonType": ["string", "null"]},
                            "size": {
                                "bsonType": ["string", "null"],
                                "enum": ["startup", "small", "medium", "large", "enterprise"]
                            },
                            "industry": {
                                "bsonType": ["string", "null"],
                                "enum": ["technology", "finance", "healthcare", "education", "retail", "manufacturing", "consulting", "media", "real_estate", "transportation", "energy", "government", "non_profit", "other"]
                            },
                            "founded_year": {
                                "bsonType": ["int", "null"],
                                "minimum": 1800,
                                "maximum": 2030
                            },
                            "headquarters": {
                                "bsonType": ["object", "null"],
                                "properties": {
                                    "street": {"bsonType": ["string", "null"]},
                                    "city": {"bsonType": ["string", "null"]},
                                    "state": {"bsonType": ["string", "null"]},
                                    "country": {"bsonType": "string"},
                                    "postal_code": {"bsonType": ["string", "null"]},
                                    "coordinates": {
                                        "bsonType": ["object", "null"],
                                        "properties": {
                                            "latitude": {
                                                "bsonType": "double",
                                                "minimum": -90,
                                                "maximum": 90
                                            },
                                            "longitude": {
                                                "bsonType": "double",
                                                "minimum": -180,
                                                "maximum": 180
                                            }
                                        }
                                    }
                                }
                            },
                            "rating": {
                                "bsonType": ["double", "null"],
                                "minimum": 0,
                                "maximum": 5
                            },
                            "employee_count": {
                                "bsonType": ["int", "null"],
                                "minimum": 0
                            }
                        }
                    },
                    "posted_date": {
                        "bsonType": ["date", "null"],
                        "description": "Original posting date"
                    },
                    "expires_date": {
                        "bsonType": ["date", "null"],
                        "description": "Job expiration date"
                    },
                    "posted_by": {
                        "bsonType": ["objectId", "null"],
                        "description": "User ID who posted the job"
                    },
                    "view_count": {
                        "bsonType": "int",
                        "minimum": 0,
                        "default": 0
                    },
                    "application_count": {
                        "bsonType": "int",
                        "minimum": 0,
                        "default": 0
                    },
                    "relevance_score": {
                        "bsonType": ["double", "null"],
                        "minimum": 0,
                        "maximum": 1,
                        "description": "AI-calculated relevance score"
                    },
                    "match_score": {
                        "bsonType": ["double", "null"],
                        "minimum": 0,
                        "maximum": 1,
                        "description": "User-specific match score"
                    },
                    "tags": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"},
                        "description": "Job tags for categorization"
                    },
                    "keywords": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"},
                        "description": "SEO keywords"
                    },
                    "is_featured": {
                        "bsonType": "bool",
                        "default": False
                    },
                    "is_urgent": {
                        "bsonType": "bool",
                        "default": False
                    },
                    "internal_notes": {
                        "bsonType": ["string", "null"],
                        "description": "Internal admin notes"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Record creation timestamp"
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
            # Text search index
            IndexModel([
                ("title", TEXT),
                ("description", TEXT),
                ("company_name", TEXT),
                ("skills_required", TEXT),
                ("skills_preferred", TEXT)
            ], name="job_text_search_idx"),
            
            # Primary query indexes
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("source", ASCENDING)], name="source_idx"),
            IndexModel([("location", ASCENDING)], name="location_idx"),
            IndexModel([("company_name", ASCENDING)], name="company_name_idx"),
            IndexModel([("employment_type", ASCENDING)], name="employment_type_idx"),
            IndexModel([("work_arrangement", ASCENDING)], name="work_arrangement_idx"),
            IndexModel([("experience_level", ASCENDING)], name="experience_level_idx"),
            
            # Date-based indexes
            IndexModel([("posted_date", DESCENDING)], name="posted_date_desc_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_desc_idx"),
            IndexModel([("expires_date", ASCENDING)], name="expires_date_asc_idx"),
            IndexModel([("application_deadline", ASCENDING)], name="application_deadline_asc_idx"),
            
            # Relevance and matching
            IndexModel([("relevance_score", DESCENDING)], name="relevance_score_desc_idx"),
            IndexModel([("match_score", DESCENDING)], name="match_score_desc_idx"),
            
            # Skills indexes
            IndexModel([("skills_required", ASCENDING)], name="skills_required_idx"),
            IndexModel([("skills_preferred", ASCENDING)], name="skills_preferred_idx"),
            
            # Salary range indexes
            IndexModel([("salary_range.min_amount", ASCENDING)], name="salary_min_asc_idx"),
            IndexModel([("salary_range.max_amount", DESCENDING)], name="salary_max_desc_idx"),
            IndexModel([("salary_range.currency", ASCENDING)], name="salary_currency_idx"),
            
            # Analytics indexes
            IndexModel([("view_count", DESCENDING)], name="view_count_desc_idx"),
            IndexModel([("application_count", DESCENDING)], name="application_count_desc_idx"),
            
            # External source tracking
            IndexModel([("source", ASCENDING), ("external_id", ASCENDING)], name="source_external_id_idx"),
            IndexModel([("external_url", ASCENDING)], name="external_url_idx"),
            
            # Company information
            IndexModel([("company_info.industry", ASCENDING)], name="company_industry_idx"),
            IndexModel([("company_info.size", ASCENDING)], name="company_size_idx"),
            IndexModel([("company_info.rating", DESCENDING)], name="company_rating_desc_idx"),
            
            # Geographic indexes
            IndexModel([("company_info.headquarters.coordinates", "2dsphere")], name="company_location_geo_idx"),
            
            # Admin and moderation
            IndexModel([("posted_by", ASCENDING)], name="posted_by_idx"),
            IndexModel([("is_featured", ASCENDING)], name="is_featured_idx"),
            IndexModel([("is_urgent", ASCENDING)], name="is_urgent_idx"),
            IndexModel([("tags", ASCENDING)], name="tags_idx"),
            
            # Compound indexes for complex queries
            IndexModel([
                ("status", ASCENDING),
                ("posted_date", DESCENDING)
            ], name="status_posted_date_idx"),
            
            IndexModel([
                ("location", ASCENDING),
                ("employment_type", ASCENDING),
                ("experience_level", ASCENDING)
            ], name="location_employment_experience_idx"),
            
            IndexModel([
                ("company_name", ASCENDING),
                ("status", ASCENDING),
                ("posted_date", DESCENDING)
            ], name="company_status_posted_idx"),
            
            IndexModel([
                ("skills_required", ASCENDING),
                ("experience_level", ASCENDING),
                ("salary_range.min_amount", ASCENDING)
            ], name="skills_experience_salary_idx"),
            
            IndexModel([
                ("source", ASCENDING),
                ("status", ASCENDING),
                ("created_at", DESCENDING)
            ], name="source_status_created_idx")
        ]
    
    # Default values for new documents
    @staticmethod
    def get_defaults() -> Dict[str, Any]:
        return {
            "status": "active",
            "source": "manual",
            "view_count": 0,
            "application_count": 0,
            "requirements": [],
            "benefits": [],
            "skills_required": [],
            "skills_preferred": [],
            "tags": [],
            "keywords": [],
            "is_featured": False,
            "is_urgent": False
        }
    
    # Aggregation pipelines
    @staticmethod
    def get_job_stats_pipeline(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Aggregation pipeline for job statistics"""
        match_stage = {"$match": filters} if filters else {"$match": {}}
        
        return [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_jobs": {"$sum": 1},
                    "active_jobs": {
                        "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                    },
                    "avg_salary_min": {"$avg": "$salary_range.min_amount"},
                    "avg_salary_max": {"$avg": "$salary_range.max_amount"},
                    "total_views": {"$sum": "$view_count"},
                    "total_applications": {"$sum": "$application_count"}
                }
            }
        ]
    
    @staticmethod
    def get_top_companies_pipeline(limit: int = 10) -> List[Dict[str, Any]]:
        """Aggregation pipeline for top companies by job count"""
        return [
            {"$match": {"status": "active"}},
            {
                "$group": {
                    "_id": "$company_name",
                    "job_count": {"$sum": 1},
                    "total_views": {"$sum": "$view_count"},
                    "total_applications": {"$sum": "$application_count"},
                    "avg_salary_min": {"$avg": "$salary_range.min_amount"},
                    "industries": {"$addToSet": "$company_info.industry"},
                    "locations": {"$addToSet": "$location"}
                }
            },
            {"$sort": {"job_count": -1}},
            {"$limit": limit}
        ]
    
    @staticmethod
    def get_skills_distribution_pipeline() -> List[Dict[str, Any]]:
        """Aggregation pipeline for skills distribution"""
        return [
            {"$match": {"status": "active"}},
            {"$unwind": "$skills_required"},
            {
                "$group": {
                    "_id": {"$toLower": "$skills_required"},
                    "count": {"$sum": 1},
                    "avg_salary": {"$avg": "$salary_range.min_amount"}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 50}
        ]
    
    @staticmethod
    def get_salary_distribution_pipeline() -> List[Dict[str, Any]]:
        """Aggregation pipeline for salary distribution"""
        return [
            {
                "$match": {
                    "status": "active",
                    "salary_range.min_amount": {"$exists": True, "$ne": None}
                }
            },
            {
                "$bucket": {
                    "groupBy": "$salary_range.min_amount",
                    "boundaries": [0, 30000, 50000, 75000, 100000, 150000, 200000, 300000, 500000],
                    "default": "500000+",
                    "output": {
                        "count": {"$sum": 1},
                        "jobs": {"$push": {"title": "$title", "company": "$company_name"}}
                    }
                }
            }
        ]
    
    @staticmethod
    def get_location_jobs_pipeline() -> List[Dict[str, Any]]:
        """Aggregation pipeline for jobs by location"""
        return [
            {"$match": {"status": "active"}},
            {
                "$group": {
                    "_id": "$location",
                    "job_count": {"$sum": 1},
                    "companies": {"$addToSet": "$company_name"},
                    "avg_salary": {"$avg": "$salary_range.min_amount"},
                    "remote_jobs": {
                        "$sum": {"$cond": [{"$eq": ["$work_arrangement", "remote"]}, 1, 0]}
                    }
                }
            },
            {"$sort": {"job_count": -1}},
            {"$limit": 20}
        ]


# Collection schema for MongoDB validation
job_collection_schema = {
    "validator": JobSchema.get_validator(),
    "validationLevel": "strict",
    "validationAction": "error"
}

# Export schema class and collection schema
__all__ = ["JobSchema", "job_collection_schema"]