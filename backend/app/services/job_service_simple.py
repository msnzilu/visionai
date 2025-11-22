# Complete fixed version of job_service.py
# This file has been restored with all necessary fixes

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging
from difflib import SequenceMatcher
from app.integrations.job_boards.generic_scraper import GenericJobScraper
from app.models.job import (
    Job, JobCreate, JobUpdate, JobResponse, JobSearch,
    JobFilter, JobListResponse, JobStatus, JobSource
)
from app.integrations.job_boards.indeed import IndeedClient
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class JobService:
    """Service for job-related operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.jobs_collection = db.jobs
        self.generic_scraper = GenericJobScraper()
        
        try:
            from app.integrations.job_boards.remoteok_client import RemoteOKClient
            self.remoteok_client = RemoteOKClient()
        except ImportError:
            logger.warning("RemoteOK client not available")
            self.remoteok_client = None
        
    async def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        filters: Optional[JobFilter] = None,
        page: int = 1,
        size: int = 20,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search jobs from database only - no external scraping"""
        
        # Build MongoDB query
        mongo_query = {"status": JobStatus.ACTIVE}
        
        # Search by query (title, description, company)
        if query:
            mongo_query["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"company_name": {"$regex": query, "$options": "i"}}
            ]
        
        # Location filter
        if location:
            if filters and filters.remote_only:
                from app.models.job import WorkArrangement
                mongo_query["work_arrangement"] = WorkArrangement.REMOTE
            else:
                mongo_query["location"] = {"$regex": location, "$options": "i"}
        
        # Employment type filter
        if filters and filters.employment_types:
            mongo_query["employment_type"] = {"$in": filters.employment_types}
        
        # Work arrangement filter
        if filters and filters.work_arrangements:
            mongo_query["work_arrangement"] = {"$in": filters.work_arrangements}
        
        # Experience level filter
        if filters and filters.experience_levels:
            mongo_query["experience_level"] = {"$in": filters.experience_levels}
        
        # Salary range filter
        if filters and (filters.salary_min or filters.salary_max):
            salary_query = {}
            if filters.salary_min:
                salary_query["$gte"] = filters.salary_min
            if filters.salary_max:
                salary_query["$lte"] = filters.salary_max
            mongo_query["salary_range.min_amount"] = salary_query
        
        # Posted date filter
        if filters and filters.posted_after:
            mongo_query["posted_date"] = {"$gte": filters.posted_after}
        
        # Get total count BEFORE pagination
        total = await self.jobs_collection.count_documents(mongo_query)
        
        # Apply pagination
        skip = (page - 1) * size
        cursor = self.jobs_collection.find(mongo_query)
        cursor = cursor.sort("created_at", -1)
        cursor = cursor.skip(skip).limit(size)
        
        # Fetch jobs
        jobs_data = await cursor.to_list(length=size)
        jobs = [self._doc_to_job_response(doc) for doc in jobs_data]
        
        # Calculate pagination info
        pages = (total + size - 1) // size if total > 0 else 0
        
        # Build result
        result = {
            "jobs": jobs,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
            "filters_applied": filters.dict() if filters else {},
            "search_query": query
        }
        
        logger.info(f"Database search: query='{query}', location='{location}', found {total} jobs")
        
        return result
    
    def _doc_to_job_response(self, doc: Dict[str, Any]) -> JobResponse:
        """Convert MongoDB document to JobResponse with data cleaning"""
        
        doc["id"] = str(doc.pop("_id"))
        
        # Provide defaults for optional fields
        doc.setdefault("employment_type", None)
        doc.setdefault("work_arrangement", None)
        doc.setdefault("experience_level", None)
        doc.setdefault("salary_range", None)
        doc.setdefault("requirements", [])
        doc.setdefault("benefits", [])
        doc.setdefault("skills_required", [])
        doc.setdefault("skills_preferred", [])
        doc.setdefault("external_url", None)
        doc.setdefault("company_info", None)
        doc.setdefault("posted_date", None)
        doc.setdefault("application_deadline", None)
        doc.setdefault("relevance_score", None)
        doc.setdefault("match_score", None)
        doc.setdefault("view_count", 0)
        doc.setdefault("application_count", 0)
        doc.setdefault("is_featured", False)
        doc.setdefault("tags", [])
        
        # Clean invalid data formats
        if isinstance(doc.get("benefits"), list) and doc["benefits"]:
            if isinstance(doc["benefits"][0], str):
                doc["benefits"] = []
        
        if isinstance(doc.get("requirements"), list) and doc["requirements"]:
            if isinstance(doc["requirements"][0], str):
                doc["requirements"] = []
        
        return JobResponse(**doc)
    
    async def get_job_by_id(self, job_id: str) -> Optional[JobResponse]:
        """Get job by ID"""
        try:
            doc = await self.jobs_collection.find_one({"_id": ObjectId(job_id)})
            if doc:
                return self._doc_to_job_response(doc)
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
        return None


job_service: Optional[JobService] = None

def get_job_service(db: AsyncIOMotorDatabase) -> JobService:
    """Get or create job service instance"""
    global job_service
    if not job_service:
        job_service = JobService(db)
    return job_service
