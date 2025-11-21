# backend/app/services/job_service.py
"""
Job service - Core business logic for job management
"""

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
# from app.integrations.job_boards.linkedin import LinkedInScraper
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class JobService:
    """Service for job-related operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.jobs_collection = db.jobs
        self.generic_scraper = GenericJobScraper()
        
        # Add RemoteOK JSON API client (reliable, no auth needed)
        try:
            from app.integrations.job_boards.remoteok_client import RemoteOKClient
            self.remoteok_client = RemoteOKClient()
        except ImportError:
            logger.warning("RemoteOK client not available")
            self.remoteok_client = None
        
    # async def search_jobs(
    #     self,
    #     query: Optional[str] = None,
    #     location: Optional[str] = None,
    #     filters: Optional[JobFilter] = None,
    #     page: int = 1,
    #     size: int = 20,
    #     user_id: Optional[str] = None
    # ) -> Dict[str, Any]:
    #     """Search jobs - always scrape fresh results, then query database"""
        
    #     # Build MongoDB query
    #     mongo_query = {"status": JobStatus.ACTIVE}
        
    #     if query:
    #         mongo_query["$text"] = {"$search": query}
        
    #     if location and filters and not filters.remote_only:
    #         mongo_query["location"] = {"$regex": location, "$options": "i"}
        
    #     if filters and filters.remote_only:
    #         from app.models.job import WorkArrangement
    #         mongo_query["work_arrangement"] = WorkArrangement.REMOTE
        
    #     if filters and filters.employment_types:
    #         mongo_query["employment_type"] = {"$in": filters.employment_types}
        
    #     if filters and filters.experience_levels:
    #         mongo_query["experience_level"] = {"$in": filters.experience_levels}
        
    #     if filters and (filters.salary_min or filters.salary_max):
    #         salary_query = {}
    #         if filters.salary_min:
    #             salary_query["$gte"] = filters.salary_min
    #         if filters.salary_max:
    #             salary_query["$lte"] = filters.salary_max
    #         mongo_query["salary_range.min_amount"] = salary_query
        
    #     if filters and filters.posted_after:
    #         mongo_query["posted_date"] = {"$gte": filters.posted_after}
        
    #     if filters and filters.skills:
    #         mongo_query["skills_required"] = {"$in": filters.skills}
        
    #     # Always trigger scraping for fresh results when query/location provided
    #     if query or location:
    #         logger.info(f"Triggering scrape for: {query} in {location}")
    #         await self._scrape_and_populate(query or "jobs", location or "remote")
        
    #     # Query database for total count
    #     total = await self.jobs_collection.count_documents(mongo_query)
        
    #     # Query database
    #     skip = (page - 1) * size
    #     cursor = self.jobs_collection.find(mongo_query)
    #     cursor = cursor.sort("created_at", -1)
    #     cursor = cursor.skip(skip).limit(size)
        
    #     jobs_data = await cursor.to_list(length=size)
    #     jobs = [self._doc_to_job_response(doc) for doc in jobs_data]
        
    #     pages = (total + size - 1) // size if total > 0 else 0
        
    #     # Build result
    #     result = {
    #         "jobs": jobs,
    #         "total": total,
    #         "page": page,
    #         "size": size,
    #         "pages": pages,
    #         "has_next": page < pages,
    #         "has_prev": page > 1,
    #         "filters_applied": filters.dict() if filters else {},
    #         "search_query": query
    #     }
        
    #     return result

    async def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        filters: Optional[JobFilter] = None,
        page: int = 1,
        size: int = 20,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search jobs - always scrape fresh results, then query database"""
        
        # Build MongoDB query
        mongo_query = {"status": JobStatus.ACTIVE}
        
        # CHANGED: Use regex instead of text search
        if query:
            mongo_query["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"company_name": {"$regex": query, "$options": "i"}}
            ]
        
        if location and filters and not filters.remote_only:
            mongo_query["location"] = {"$regex": location, "$options": "i"}
        
        if filters and filters.remote_only:
            from app.models.job import WorkArrangement
            mongo_query["work_arrangement"] = WorkArrangement.REMOTE
        
        if filters and filters.employment_types:
            mongo_query["employment_type"] = {"$in": filters.employment_types}
        
        if filters and filters.experience_levels:
            mongo_query["experience_level"] = {"$in": filters.experience_levels}
        
        if filters and (filters.salary_min or filters.salary_max):
            salary_query = {}
            if filters.salary_min:
                salary_query["$gte"] = filters.salary_min
            if filters.salary_max:
                salary_query["$lte"] = filters.salary_max
            mongo_query["salary_range.min_amount"] = salary_query
        
        skip = (page - 1) * size
        cursor = self.jobs_collection.find(mongo_query)
        cursor = cursor.sort("created_at", -1)
        cursor = cursor.skip(skip).limit(size)
        
        jobs_data = await cursor.to_list(length=size)
        jobs = [self._doc_to_job_response(doc) for doc in jobs_data]
        
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
        
        return result
    
    async def _scrape_and_populate(self, query: str, location: str) -> int:
        """Scrape jobs and populate database"""
        try:
            logger.info(f"Starting scrape for: {query} in {location}")
            
            # Get jobs from external sources
            jobs = await self.aggregate_from_sources(
                query=query,
                location=location,
                limit=50
            )
            
            if not jobs:
                logger.warning("No jobs scraped from external sources")
                return 0
            
            # Save to database
            count = await self.bulk_create_jobs(jobs)
            logger.info(f"Successfully scraped and saved {count} jobs")
            
            return count
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            return 0
    
    async def aggregate_from_sources(
        self,
        query: str,
        location: str,
        limit: int = 50
    ) -> List[JobCreate]:
        """Aggregate jobs from RemoteOK API"""
        
        all_jobs = []
        
        # Try RemoteOK JSON API (free, no auth needed)
        if self.remoteok_client:
            try:
                remoteok_results = await self.remoteok_client.search_jobs(
                    query=query,
                    limit=limit
                )
                remoteok_jobs = [
                    self.remoteok_client.normalize_job(job)
                    for job in remoteok_results
                ]
                all_jobs.extend(remoteok_jobs)
                logger.info(f"Got {len(remoteok_jobs)} jobs from RemoteOK API")
            except Exception as e:
                logger.error(f"RemoteOK API failed: {e}")
        
        # Deduplicate
        unique_jobs = self.deduplicate_jobs(all_jobs)
        
        logger.info(f"Total unique jobs aggregated: {len(unique_jobs)}")
        return unique_jobs

    
    def deduplicate_jobs(self, jobs: List[JobCreate]) -> List[JobCreate]:
        """Remove duplicate jobs based on similarity"""
        
        if not jobs:
            return []
        
        unique_jobs = []
        seen_external_ids = set()
        seen_signatures = set()
        
        for job in jobs:
            if job.external_id:
                external_key = f"{job.source}:{job.external_id}"
                if external_key in seen_external_ids:
                    continue
                seen_external_ids.add(external_key)
            
            signature = f"{job.title.lower()}|{job.company_name.lower()}"
            
            is_duplicate = False
            for seen_sig in seen_signatures:
                similarity = SequenceMatcher(None, signature, seen_sig).ratio()
                if similarity > 0.9:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_signatures.add(signature)
                unique_jobs.append(job)
        
        logger.info(f"Deduplicated {len(jobs)} jobs to {len(unique_jobs)} unique jobs")
        return unique_jobs
    
    async def create_job(self, job_data: JobCreate) -> Job:
        """Create a new job in database"""
        
        job_dict = job_data.dict()
        job_dict["created_at"] = datetime.utcnow()
        job_dict["updated_at"] = datetime.utcnow()
        job_dict["status"] = JobStatus.ACTIVE
        job_dict["view_count"] = 0
        job_dict["application_count"] = 0
        
        result = await self.jobs_collection.insert_one(job_dict)
        job_dict["_id"] = str(result.inserted_id)
        
        return Job(**job_dict)
    
    async def bulk_create_jobs(self, jobs: List[JobCreate]) -> int:
        """Bulk insert jobs, avoiding duplicates"""
        
        if not jobs:
            return 0
        
        jobs_data = []
        inserted_count = 0
        
        for job in jobs:
            # Check if job already exists (by external_id or title+company)
            existing = None
            if job.external_id:
                existing = await self.jobs_collection.find_one({
                    "external_id": job.external_id,
                    "source": job.source
                })
            
            if not existing:
                # Check by title + company combination
                existing = await self.jobs_collection.find_one({
                    "title": job.title,
                    "company_name": job.company_name
                })
            
            if existing:
                logger.debug(f"Skipping duplicate job: {job.title} at {job.company_name}")
                continue
            
            job_dict = job.dict()
            job_dict["created_at"] = datetime.utcnow()
            job_dict["updated_at"] = datetime.utcnow()
            job_dict["status"] = JobStatus.ACTIVE
            job_dict["view_count"] = 0
            job_dict["application_count"] = 0
            jobs_data.append(job_dict)
        
        if jobs_data:
            try:
                result = await self.jobs_collection.insert_many(
                    jobs_data,
                    ordered=False
                )
                inserted_count = len(result.inserted_ids)
                logger.info(f"Bulk inserted {inserted_count} new jobs")
            except Exception as e:
                logger.error(f"Bulk insert error: {e}")
        
        return inserted_count
    
    async def get_job_by_id(self, job_id: str) -> Optional[JobResponse]:
        """Get job by ID"""
        
        try:
            doc = await self.jobs_collection.find_one({"_id": ObjectId(job_id)})
            if doc:
                return self._doc_to_job_response(doc)
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
        
        return None
    
    async def increment_view_count(self, job_id: str):
        """Increment job view count"""
        
        await self.jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$inc": {"view_count": 1}}
        )
    
    async def expire_old_jobs(self, days: int = 90) -> int:
        """Mark old jobs as expired"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.jobs_collection.update_many(
            {
                "created_at": {"$lt": cutoff_date},
                "status": JobStatus.ACTIVE
            },
            {
                "$set": {
                    "status": JobStatus.EXPIRED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Expired {result.modified_count} old jobs")
        return result.modified_count
    
    def _doc_to_job_response(self, doc: Dict[str, Any]) -> JobResponse:
        """Convert MongoDB document to JobResponse"""
        
        doc["id"] = str(doc.pop("_id"))
        return JobResponse(**doc)
    
    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'linkedin_scraper') and self.linkedin_scraper:
            await self.linkedin_scraper.close()


job_service: Optional[JobService] = None

def get_job_service(db: AsyncIOMotorDatabase) -> JobService:
    """Get or create job service instance"""
    global job_service
    if not job_service:
        job_service = JobService(db)
    return job_service