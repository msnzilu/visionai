# backend/app/schemas/application.py
"""
Application collection database schema for MongoDB
"""

from typing import Dict, Any, List
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT


class ApplicationSchema:
    """Application collection schema definitions"""
    
    # Collection name
    COLLECTION_NAME = "applications"
    
    # MongoDB JSON Schema validator
    @staticmethod
    def get_validator() -> Dict[str, Any]:
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "job_id", "user_id", "status", "source", 
                    "created_at", "updated_at"
                ],
                "properties": {
                    "job_id": {
                        "bsonType": "objectId",
                        "description": "Reference to job document"
                    },
                    "user_id": {
                        "bsonType": "objectId",
                        "description": "Reference to user document"
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": [
                            "draft", "submitted", "under_review", "interview_scheduled",
                            "interview_completed", "second_round", "final_round",
                            "offer_received", "offer_accepted", "offer_declined",
                            "rejected", "withdrawn", "on_hold", "archived"
                        ],
                        "description": "Current application status"
                    },
                    "source": {
                        "bsonType": "string",
                        "enum": ["manual", "platform", "auto_apply", "referral", "direct", "recruiter"],
                        "description": "How the application was submitted"
                    },
                    "applied_date": {
                        "bsonType": ["date", "null"],
                        "description": "Date when application was submitted"
                    },
                    "custom_cv_content": {
                        "bsonType": ["string", "null"],
                        "description": "Customized CV content for this application"
                    },
                    "cover_letter_content": {
                        "bsonType": ["string", "null"],
                        "description": "Cover letter content"
                    },
                    "additional_notes": {
                        "bsonType": ["string", "null"],
                        "maxLength": 2000,
                        "description": "Additional notes from user"
                    },
                    "salary_expectation": {
                        "bsonType": ["double", "null"],
                        "minimum": 0,
                        "description": "User's salary expectation"
                    },
                    "availability_date": {
                        "bsonType": ["date", "null"],
                        "description": "When user can start"
                    },
                    "referral_source": {
                        "bsonType": ["string", "null"],
                        "description": "How user found this job"
                    },
                    "priority": {
                        "bsonType": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "default": "medium"
                    },
                    "documents": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["type", "filename", "file_path"],
                            "properties": {
                                "id": {"bsonType": ["string", "null"]},
                                "type": {
                                    "bsonType": "string",
                                    "enum": ["resume", "cv", "cover_letter", "portfolio", "transcript", "certificate", "reference", "writing_sample", "other"]
                                },
                                "filename": {"bsonType": "string"},
                                "file_path": {"bsonType": "string"},
                                "file_size": {"bsonType": "long"},
                                "content_type": {"bsonType": "string"},
                                "version": {
                                    "bsonType": "int",
                                    "minimum": 1,
                                    "default": 1
                                },
                                "is_customized": {"bsonType": "bool"},
                                "customization_notes": {"bsonType": ["string", "null"]},
                                "generated_by_ai": {"bsonType": "bool"},
                                "upload_date": {"bsonType": "date"},
                                "last_modified": {"bsonType": "date"}
                            }
                        }
                    },
                    "custom_cv": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "original_cv_id": {"bsonType": "string"},
                            "job_id": {"bsonType": "objectId"},
                            "customized_content": {"bsonType": "string"},
                            "customization_prompt": {"bsonType": "string"},
                            "ai_model_used": {"bsonType": ["string", "null"]},
                            "customization_score": {
                                "bsonType": ["double", "null"],
                                "minimum": 0,
                                "maximum": 1
                            },
                            "highlighted_skills": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            },
                            "emphasized_experience": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            },
                            "created_at": {"bsonType": "date"}
                        }
                    },
                    "cover_letter": {
                        "bsonType": ["object", "null"],
                        "properties": {
                            "job_id": {"bsonType": "objectId"},
                            "user_id": {"bsonType": "objectId"},
                            "content": {"bsonType": "string"},
                            "tone": {
                                "bsonType": "string",
                                "enum": ["professional", "casual", "enthusiastic", "formal"],
                                "default": "professional"
                            },
                            "template_used": {"bsonType": ["string", "null"]},
                            "ai_generated": {"bsonType": "bool"},
                            "ai_model_used": {"bsonType": ["string", "null"]},
                            "generation_prompt": {"bsonType": ["string", "null"]},
                            "word_count": {"bsonType": ["int", "null"]},
                            "created_at": {"bsonType": "date"},
                            "last_modified": {"bsonType": "date"}
                        }
                    },
                    "communications": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["type", "content", "timestamp"],
                            "properties": {
                                "type": {
                                    "bsonType": "string",
                                    "enum": ["email", "phone", "sms", "in_person", "video_call", "linkedin", "platform_message", "other"]
                                },
                                "direction": {
                                    "bsonType": "string",
                                    "enum": ["inbound", "outbound"],
                                    "default": "outbound"
                                },
                                "subject": {"bsonType": ["string", "null"]},
                                "content": {"bsonType": "string"},
                                "contact_person": {"bsonType": ["string", "null"]},
                                "contact_email": {"bsonType": ["string", "null"]},
                                "contact_phone": {"bsonType": ["string", "null"]},
                                "attachments": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "timestamp": {"bsonType": "date"},
                                "follow_up_required": {"bsonType": "bool"},
                                "follow_up_date": {"bsonType": ["date", "null"]},
                                "tags": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                }
                            }
                        }
                    },
                    "interviews": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["type", "scheduled_date"],
                            "properties": {
                                "type": {
                                    "bsonType": "string",
                                    "enum": ["phone_screening", "video_call", "in_person", "technical", "behavioral", "panel", "group", "presentation", "case_study", "coding_challenge"]
                                },
                                "scheduled_date": {"bsonType": "date"},
                                "duration_minutes": {"bsonType": ["int", "null"]},
                                "location": {"bsonType": ["string", "null"]},
                                "meeting_link": {"bsonType": ["string", "null"]},
                                "interviewer_name": {"bsonType": ["string", "null"]},
                                "interviewer_email": {"bsonType": ["string", "null"]},
                                "interviewer_title": {"bsonType": ["string", "null"]},
                                "round": {
                                    "bsonType": "int",
                                    "minimum": 1,
                                    "default": 1
                                },
                                "status": {
                                    "bsonType": "string",
                                    "enum": ["scheduled", "completed", "cancelled", "rescheduled"],
                                    "default": "scheduled"
                                },
                                "preparation_notes": {"bsonType": ["string", "null"]},
                                "interview_notes": {"bsonType": ["string", "null"]},
                                "feedback": {"bsonType": ["string", "null"]},
                                "rating": {
                                    "bsonType": ["int", "null"],
                                    "minimum": 1,
                                    "maximum": 5
                                },
                                "questions_asked": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "answers_given": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "created_at": {"bsonType": "date"},
                                "updated_at": {"bsonType": "date"}
                            }
                        }
                    },
                    "timeline": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["event_type", "description", "timestamp"],
                            "properties": {
                                "event_type": {"bsonType": "string"},
                                "status_from": {"bsonType": ["string", "null"]},
                                "status_to": {"bsonType": ["string", "null"]},
                                "description": {"bsonType": "string"},
                                "details": {"bsonType": ["object", "null"]},
                                "created_by": {"bsonType": ["string", "null"]},
                                "timestamp": {"bsonType": "date"},
                                "is_milestone": {"bsonType": "bool"},
                                "icon": {"bsonType": ["string", "null"]},
                                "color": {"bsonType": ["string", "null"]}
                            }
                        }
                    },
                    "tasks": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["title"],
                            "properties": {
                                "title": {"bsonType": "string"},
                                "description": {"bsonType": ["string", "null"]},
                                "priority": {
                                    "bsonType": "string",
                                    "enum": ["low", "medium", "high", "urgent"],
                                    "default": "medium"
                                },
                                "due_date": {"bsonType": ["date", "null"]},
                                "is_completed": {"bsonType": "bool"},
                                "completed_at": {"bsonType": ["date", "null"]},
                                "category": {"bsonType": "string"},
                                "tags": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "created_at": {"bsonType": "date"}
                            }
                        }
                    },
                    "metrics": {
                        "bsonType": "object",
                        "properties": {
                            "views": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "downloads": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "responses": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "interview_requests": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "response_rate": {
                                "bsonType": "double",
                                "minimum": 0,
                                "maximum": 1,
                                "default": 0
                            },
                            "last_updated": {"bsonType": "date"}
                        }
                    },
                    "auto_apply_used": {
                        "bsonType": "bool",
                        "default": False
                    },
                    "auto_apply_data": {
                        "bsonType": ["object", "null"],
                        "description": "Data from auto-application process"
                    },
                    "form_fields_filled": {
                        "bsonType": ["object", "null"],
                        "description": "Form fields that were auto-filled"
                    },
                    "application_url": {
                        "bsonType": ["string", "null"],
                        "description": "URL where application was submitted"
                    },
                    "confirmation_number": {
                        "bsonType": ["string", "null"],
                        "description": "Application confirmation number"
                    },
                    "job_title": {
                        "bsonType": ["string", "null"],
                        "description": "Cached job title"
                    },
                    "company_name": {
                        "bsonType": ["string", "null"],
                        "description": "Cached company name"
                    },
                    "location": {
                        "bsonType": ["string", "null"],
                        "description": "Cached job location"
                    },
                    "last_follow_up": {
                        "bsonType": ["date", "null"],
                        "description": "Last follow-up date"
                    },
                    "next_follow_up": {
                        "bsonType": ["date", "null"],
                        "description": "Scheduled next follow-up"
                    },
                    "follow_up_count": {
                        "bsonType": "int",
                        "minimum": 0,
                        "default": 0
                    },
                    "rejection_reason": {
                        "bsonType": ["string", "null"],
                        "description": "Reason for rejection if provided"
                    },
                    "offer_details": {
                        "bsonType": ["object", "null"],
                        "description": "Details of job offer if received"
                    },
                    "final_salary": {
                        "bsonType": ["double", "null"],
                        "description": "Final negotiated salary"
                    },
                    "start_date": {
                        "bsonType": ["date", "null"],
                        "description": "Actual start date if hired"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Application creation timestamp"
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
            IndexModel([("user_id", ASCENDING), ("applied_date", DESCENDING)], name="user_applied_date_idx"),
            IndexModel([("job_id", ASCENDING)], name="job_id_idx"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("source", ASCENDING)], name="source_idx"),
            IndexModel([("priority", ASCENDING)], name="priority_idx"),
            
            # Unique constraint
            IndexModel([("user_id", ASCENDING), ("job_id", ASCENDING)], unique=True, name="user_job_unique_idx"),
            
            # Date-based indexes
            IndexModel([("applied_date", DESCENDING)], name="applied_date_desc_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_desc_idx"),
            IndexModel([("updated_at", DESCENDING)], name="updated_at_desc_idx"),
            IndexModel([("next_follow_up", ASCENDING)], name="next_follow_up_asc_idx"),
            
            # Company and job info (cached)
            IndexModel([("company_name", ASCENDING)], name="company_name_idx"),
            IndexModel([("job_title", ASCENDING)], name="job_title_idx"),
            IndexModel([("location", ASCENDING)], name="location_idx"),
            
            # Interview tracking
            IndexModel([("interviews.scheduled_date", ASCENDING)], name="interview_scheduled_date_idx"),
            IndexModel([("interviews.status", ASCENDING)], name="interview_status_idx"),
            
            # Task management
            IndexModel([("tasks.due_date", ASCENDING)], name="task_due_date_idx"),
            IndexModel([("tasks.is_completed", ASCENDING)], name="task_completed_idx"),
            IndexModel([("tasks.priority", ASCENDING)], name="task_priority_idx"),
            
            # Analytics
            IndexModel([("metrics.response_rate", DESCENDING)], name="response_rate_desc_idx"),
            IndexModel([("metrics.interview_requests", DESCENDING)], name="interview_requests_desc_idx"),
            
            # Auto-application tracking
            IndexModel([("auto_apply_used", ASCENDING)], name="auto_apply_used_idx"),
            IndexModel([("application_url", ASCENDING)], name="application_url_idx"),
            
            # Communication tracking
            IndexModel([("communications.timestamp", DESCENDING)], name="communication_timestamp_desc_idx"),
            IndexModel([("communications.type", ASCENDING)], name="communication_type_idx"),
            IndexModel([("communications.follow_up_required", ASCENDING)], name="follow_up_required_idx"),
            
            # Timeline tracking
            IndexModel([("timeline.timestamp", DESCENDING)], name="timeline_timestamp_desc_idx"),
            IndexModel([("timeline.event_type", ASCENDING)], name="timeline_event_type_idx"),
            IndexModel([("timeline.is_milestone", ASCENDING)], name="timeline_milestone_idx"),
            
            # Document management
            IndexModel([("documents.type", ASCENDING)], name="document_type_idx"),
            IndexModel([("documents.upload_date", DESCENDING)], name="document_upload_date_idx"),
            IndexModel([("documents.is_customized", ASCENDING)], name="document_customized_idx"),
            
            # Compound indexes for complex queries
            IndexModel([
                ("user_id", ASCENDING),
                ("status", ASCENDING),
                ("applied_date", DESCENDING)
            ], name="user_status_applied_idx"),
            
            IndexModel([
                ("status", ASCENDING),
                ("priority", ASCENDING),
                ("next_follow_up", ASCENDING)
            ], name="status_priority_followup_idx"),
            
            IndexModel([
                ("company_name", ASCENDING),
                ("status", ASCENDING),
                ("applied_date", DESCENDING)
            ], name="company_status_applied_idx"),
            
            IndexModel([
                ("user_id", ASCENDING),
                ("interviews.scheduled_date", ASCENDING)
            ], name="user_interview_scheduled_idx"),
            
            IndexModel([
                ("user_id", ASCENDING),
                ("tasks.due_date", ASCENDING),
                ("tasks.is_completed", ASCENDING)
            ], name="user_task_due_completed_idx")
        ]
    
    # Default values for new documents
    @staticmethod
    def get_defaults() -> Dict[str, Any]:
        return {
            "status": "draft",
            "source": "manual",
            "priority": "medium",
            "documents": [],
            "communications": [],
            "interviews": [],
            "timeline": [],
            "tasks": [],
            "metrics": {
                "views": 0,
                "downloads": 0,
                "responses": 0,
                "interview_requests": 0,
                "response_rate": 0.0
            },
            "auto_apply_used": False,
            "follow_up_count": 0
        }
    
    # Aggregation pipelines
    @staticmethod
    def get_application_stats_pipeline(user_id: str = None) -> List[Dict[str, Any]]:
        """Aggregation pipeline for application statistics"""
        match_stage = {"$match": {"user_id": user_id}} if user_id else {"$match": {}}
        
        return [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total_applications": {"$sum": 1},
                    "status_counts": {
                        "$push": "$status"
                    },
                    "avg_response_rate": {"$avg": "$metrics.response_rate"},
                    "total_interviews": {"$sum": {"$size": "$interviews"}},
                    "applications_with_offers": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$status", ["offer_received", "offer_accepted"]]},
                                1, 0
                            ]
                        }
                    },
                    "auto_apply_count": {
                        "$sum": {"$cond": [{"$eq": ["$auto_apply_used", True]}, 1, 0]}
                    }
                }
            },
            {
                "$addFields": {
                    "status_distribution": {
                        "$arrayToObject": {
                            "$map": {
                                "input": {
                                    "$setUnion": "$status_counts"
                                },
                                "as": "status",
                                "in": {
                                    "k": "$status",
                                    "v": {
                                        "$size": {
                                            "$filter": {
                                                "input": "$status_counts",
                                                "cond": {"$eq": ["$this", "$status"]}
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
    def get_company_application_stats_pipeline(user_id: str = None) -> List[Dict[str, Any]]:
        """Aggregation pipeline for applications by company"""
        match_stage = {"$match": {"user_id": user_id}} if user_id else {"$match": {}}
        
        return [
            match_stage,
            {
                "$group": {
                    "_id": "$company_name",
                    "total_applications": {"$sum": 1},
                    "statuses": {"$push": "$status"},
                    "avg_response_rate": {"$avg": "$metrics.response_rate"},
                    "total_interviews": {"$sum": {"$size": "$interviews"}},
                    "latest_application": {"$max": "$applied_date"},
                    "offers_received": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$status", ["offer_received", "offer_accepted"]]},
                                1, 0
                            ]
                        }
                    }
                }
            },
            {"$sort": {"total_applications": -1}},
            {"$limit": 20}
        ]
    
    @staticmethod
    def get_timeline_pipeline(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Aggregation pipeline for application timeline"""
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return [
            {
                "$match": {
                    "user_id": user_id,
                    "timeline.timestamp": {"$gte": start_date}
                }
            },
            {"$unwind": "$timeline"},
            {
                "$match": {
                    "timeline.timestamp": {"$gte": start_date}
                }
            },
            {
                "$project": {
                    "application_id": "$_id",
                    "job_title": "$job_title",
                    "company_name": "$company_name",
                    "event": "$timeline"
                }
            },
            {"$sort": {"event.timestamp": -1}}
        ]
    
    @staticmethod
    def get_follow_up_pipeline(user_id: str = None) -> List[Dict[str, Any]]:
        """Aggregation pipeline for applications needing follow-up"""
        from datetime import datetime
        
        match_conditions = {
            "next_follow_up": {"$lte": datetime.utcnow()},
            "status": {"$in": ["submitted", "under_review", "interview_scheduled"]}
        }
        
        if user_id:
            match_conditions["user_id"] = user_id
        
        return [
            {"$match": match_conditions},
            {
                "$project": {
                    "job_title": 1,
                    "company_name": 1,
                    "status": 1,
                    "next_follow_up": 1,
                    "follow_up_count": 1,
                    "applied_date": 1,
                    "days_overdue": {
                        "$divide": [
                            {"$subtract": [datetime.utcnow(), "$next_follow_up"]},
                            86400000  # milliseconds in a day
                        ]
                    }
                }
            },
            {"$sort": {"days_overdue": -1}}
        ]
    
    @staticmethod
    def get_success_rate_pipeline(user_id: str) -> List[Dict[str, Any]]:
        """Aggregation pipeline for success rate analysis"""
        return [
            {"$match": {"user_id": user_id}},
            {
                "$facet": {
                    "by_source": [
                        {
                            "$group": {
                                "_id": "$source",
                                "total": {"$sum": 1},
                                "interviews": {
                                    "$sum": {
                                        "$cond": [
                                            {"$gt": [{"$size": "$interviews"}, 0]},
                                            1, 0
                                        ]
                                    }
                                },
                                "offers": {
                                    "$sum": {
                                        "$cond": [
                                            {"$in": ["$status", ["offer_received", "offer_accepted"]]},
                                            1, 0
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "$addFields": {
                                "interview_rate": {"$divide": ["$interviews", "$total"]},
                                "offer_rate": {"$divide": ["$offers", "$total"]}
                            }
                        }
                    ],
                    "by_month": [
                        {
                            "$group": {
                                "_id": {
                                    "year": {"$year": "$applied_date"},
                                    "month": {"$month": "$applied_date"}
                                },
                                "total": {"$sum": 1},
                                "responses": {"$sum": "$metrics.responses"},
                                "interviews": {
                                    "$sum": {
                                        "$cond": [
                                            {"$gt": [{"$size": "$interviews"}, 0]},
                                            1, 0
                                        ]
                                    }
                                }
                            }
                        },
                        {"$sort": {"_id.year": 1, "_id.month": 1}}
                    ]
                }
            }
        ]


# Collection schema for MongoDB validation
application_collection_schema = {
    "validator": ApplicationSchema.get_validator(),
    "validationLevel": "strict", 
    "validationAction": "error"
}

# Export schema class and collection schema
__all__ = ["ApplicationSchema", "application_collection_schema"]