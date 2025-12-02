# backend/app/integrations/job_boards/indeed.py
"""
Indeed API integration for job search
"""

import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from app.models.job import (
    JobCreate, JobSource, EmploymentType, 
    WorkArrangement, SalaryRange
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class IndeedClient:
    """Indeed API client for job search"""
    
    def __init__(self):
        self.base_url = "https://api.indeed.com/ads/apisearch"
        self.publisher_id = settings.INDEED_PUBLISHER_ID
        self.api_key = getattr(settings, 'INDEED_API_KEY', None)
        
    async def search_jobs(
        self,
        query: str,
        location: str,
        radius: int = 25,
        employment_type: Optional[str] = None,
        limit: int = 25,
        start: int = 0
    ) -> List[Dict[str, Any]]:
        """Search jobs on Indeed API"""
        
        params = {
            "publisher": self.publisher_id,
            "q": query,
            "l": location,
            "radius": radius,
            "limit": min(limit, 25),  # Indeed API max is 25
            "start": start,
            "format": "json",
            "v": "2",
            "userip": "1.2.3.4",  # Required by Indeed
            "useragent": "Mozilla/5.0"
        }
        
        if employment_type:
            params["jt"] = employment_type
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Indeed API returned {len(data.get('results', []))} results")
                return data.get("results", [])
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Indeed API HTTP error: {e.response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Indeed API error: {str(e)}")
                return []
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> JobCreate:
        """Convert Indeed job format to JobCreate model"""
        
        # Extract salary if available
        salary_range = None
        if raw_job.get("salary"):
            salary_range = self._parse_salary(raw_job.get("salary"))
        
        # Map employment type
        employment_type = self._map_employment_type(raw_job.get("jobtype"))
        
        # Determine work arrangement
        work_arrangement = None
        snippet = raw_job.get("snippet", "").lower()
        if "remote" in snippet:
            work_arrangement = WorkArrangement.REMOTE
        elif "hybrid" in snippet:
            work_arrangement = WorkArrangement.HYBRID
        
        return JobCreate(
            title=raw_job.get("jobtitle", ""),
            description=raw_job.get("snippet", ""),
            company_name=raw_job.get("company", ""),
            location=raw_job.get("formattedLocation", raw_job.get("city", "")),
            source=JobSource.INDEED,
            external_id=raw_job.get("jobkey"),
            external_url=raw_job.get("url"),
            posted_date=self._parse_date(raw_job.get("date")),
            employment_type=employment_type,
            work_arrangement=work_arrangement,
            salary_range=salary_range,
            skills_required=self._extract_skills(raw_job.get("snippet", ""))
        )
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse Indeed relative date format"""
        if not date_str:
            return datetime.utcnow()
        
        date_str = date_str.lower()
        now = datetime.utcnow()
        
        # Handle "Just posted", "Today", etc.
        if any(term in date_str for term in ["just posted", "today"]):
            return now
        elif "yesterday" in date_str:
            return now - timedelta(days=1)
        elif "days ago" in date_str:
            try:
                days = int(date_str.split()[0])
                return now - timedelta(days=days)
            except:
                pass
        
        return now
    
    def _map_employment_type(self, job_type: str) -> Optional[EmploymentType]:
        """Map Indeed job type to EmploymentType enum"""
        if not job_type:
            return None
            
        mapping = {
            "fulltime": EmploymentType.FULL_TIME,
            "parttime": EmploymentType.PART_TIME,
            "contract": EmploymentType.CONTRACT,
            "temporary": EmploymentType.TEMPORARY,
            "internship": EmploymentType.INTERNSHIP,
        }
        return mapping.get(job_type.lower())
    
    def _parse_salary(self, salary_str: str) -> Optional[SalaryRange]:
        """Parse salary string to SalaryRange"""
        if not salary_str:
            return None
        
        import re
        
        # Extract numbers from salary string
        numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d{2})?', salary_str.replace(',', ''))
        
        if not numbers:
            return None
        
        # Determine period
        period = "yearly"
        if "hour" in salary_str.lower():
            period = "hourly"
        elif "month" in salary_str.lower():
            period = "monthly"
        
        # Parse range or single value
        try:
            if len(numbers) >= 2:
                return SalaryRange(
                    min_amount=float(numbers[0]),
                    max_amount=float(numbers[1]),
                    period=period,
                    currency="USD"
                )
            elif len(numbers) == 1:
                return SalaryRange(
                    min_amount=float(numbers[0]),
                    period=period,
                    currency="USD"
                )
        except:
            pass
        
        return None
    
    def _extract_skills(self, description: str) -> List[str]:
        """Extract common tech skills from description"""
        if not description:
            return []
        
        description_lower = description.lower()
        
        # Common skills to look for
        common_skills = [
            "python", "javascript", "java", "c++", "c#", "ruby", "php",
            "react", "angular", "vue", "node.js", "django", "flask",
            "sql", "nosql", "mongodb", "postgresql", "mysql",
            "aws", "azure", "gcp", "docker", "kubernetes",
            "git", "agile", "scrum", "rest api", "graphql"
        ]
        
        found_skills = [
            skill for skill in common_skills 
            if skill in description_lower
        ]
        
        return found_skills[:10]  # Limit to 10 skills