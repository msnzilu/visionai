# backend/app/services/matching_service.py
"""
Job matching service - Score and rank jobs based on user profile
"""

from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import logging

from app.models.job import (
    Job, JobResponse, JobMatch, ExperienceLevel, 
    WorkArrangement, EmploymentType
)
from app.models.user import User

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for matching jobs to user profiles"""
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="job_platform")
        self.location_cache = {}
        
    async def calculate_match_score(
        self,
        user: Union[User, Dict],  # Can be dict or User model
        job: JobResponse
    ) -> Tuple[float, JobMatch]:
        """Calculate comprehensive match score"""
        
        # Handle both dict and User model
        if isinstance(user, dict):
            user_skills = set(s.lower() for s in (user.get('skills') or []))
            user_location = user.get('location')
            user_experience_years = user.get('years_of_experience') or 0
            user_salary_expectation = user.get('salary_expectation')
            user_id = str(user.get('_id') or user.get('id'))
        else:
            user_skills = set(s.lower() for s in (user.skills or []))
            user_location = user.location
            user_experience_years = user.years_of_experience or 0
            user_salary_expectation = user.salary_expectation
            user_id = str(user.id)
        
        skills_score = self._calculate_skills_match(
            user_skills, 
            set(s.lower() for s in job.skills_required)
        )
        
        location_score = await self._calculate_location_match(
            user_location,
            job.location,
            job.work_arrangement
        )
        
        experience_score = self._calculate_experience_match(
            user_experience_years,
            job.experience_level
        )
        
        salary_score = self._calculate_salary_match(
            user_salary_expectation,
            job.salary_range
        )
        
        composite_score = (
            skills_score * 0.40 +
            location_score * 0.25 +
            experience_score * 0.20 +
            salary_score * 0.15
        )
        
        matching_skills = list(user_skills & set(s.lower() for s in job.skills_required))
        missing_skills = list(set(s.lower() for s in job.skills_required) - user_skills)
        
        match_reasons = self._generate_match_reasons(
            skills_score, location_score, experience_score, 
            salary_score, matching_skills
        )
        
        recommendations = self._generate_recommendations(
            missing_skills, experience_score
        )
        
        job_match = JobMatch(
            job_id=job.id,
            user_id=user_id,
            match_score=round(composite_score, 2),
            relevance_score=round(skills_score, 2),
            matching_skills=matching_skills[:5],
            missing_skills=missing_skills[:5],
            match_reasons=match_reasons,
            recommendations=recommendations
        )
        
        return round(composite_score, 2), job_match
    
    def _calculate_skills_match(self, user_skills: set, job_skills: set) -> float:
        if not job_skills:
            return 0.5
        if not user_skills:
            return 0.0
        
        intersection = len(user_skills & job_skills)
        union = len(user_skills | job_skills)
        
        return intersection / union if union > 0 else 0.0
    
    async def _calculate_location_match(
        self,
        user_location: Optional[str],
        job_location: str,
        work_arrangement: Optional[WorkArrangement],
        max_distance: float = 50.0
    ) -> float:
        if work_arrangement == WorkArrangement.REMOTE:
            return 1.0
        
        if not user_location:
            return 0.7
        
        if user_location.lower() in job_location.lower():
            return 1.0
        
        try:
            user_coords = await self._get_coordinates(user_location)
            job_coords = await self._get_coordinates(job_location)
            
            if user_coords and job_coords:
                distance = geodesic(user_coords, job_coords).miles
                
                if distance <= max_distance:
                    return max(0.0, 1.0 - (distance / max_distance))
        except Exception as e:
            logger.warning(f"Location calculation error: {e}")
        
        return 0.3
    
    async def _get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        if location in self.location_cache:
            return self.location_cache[location]
        
        try:
            geo_location = self.geocoder.geocode(location)
            if geo_location:
                coords = (geo_location.latitude, geo_location.longitude)
                self.location_cache[location] = coords
                return coords
        except Exception as e:
            logger.error(f"Geocoding error for {location}: {e}")
        
        return None
    
    def _calculate_experience_match(
        self,
        user_years: int,
        job_level: Optional[ExperienceLevel]
    ) -> float:
        if not job_level:
            return 0.7
        
        level_ranges = {
            ExperienceLevel.ENTRY_LEVEL: (0, 2),
            ExperienceLevel.JUNIOR: (1, 3),
            ExperienceLevel.MID_LEVEL: (3, 6),
            ExperienceLevel.SENIOR: (6, 10),
            ExperienceLevel.LEAD: (8, 15),
            ExperienceLevel.PRINCIPAL: (10, 20),
            ExperienceLevel.DIRECTOR: (12, 25),
            ExperienceLevel.EXECUTIVE: (15, 40)
        }
        
        min_years, max_years = level_ranges.get(job_level, (0, 100))
        
        if min_years <= user_years <= max_years:
            return 1.0
        
        if user_years < min_years:
            gap = min_years - user_years
            return max(0.0, 1.0 - (gap * 0.2))
        
        if user_years > max_years:
            excess = user_years - max_years
            return max(0.5, 1.0 - (excess * 0.1))
        
        return 0.5
    
    def _calculate_salary_match(
        self,
        user_expectation: Optional[float],
        job_salary: Optional[object]
    ) -> float:
        if not user_expectation or not job_salary:
            return 0.7
        
        job_min = getattr(job_salary, 'min_amount', None)
        job_max = getattr(job_salary, 'max_amount', None)
        
        if not job_min and not job_max:
            return 0.7
        
        if job_min and job_max:
            if job_min <= user_expectation <= job_max:
                return 1.0
            elif user_expectation < job_min:
                return 0.9
            else:
                diff_pct = (user_expectation - job_max) / job_max
                return max(0.0, 1.0 - diff_pct)
        
        if job_min:
            return 0.9 if user_expectation >= job_min else 0.6
        
        if job_max:
            return 0.9 if user_expectation <= job_max else 0.5
        
        return 0.7
    
    def _generate_match_reasons(
        self,
        skills_score: float,
        location_score: float,
        experience_score: float,
        salary_score: float,
        matching_skills: List[str]
    ) -> List[str]:
        reasons = []
        
        if skills_score > 0.7 and matching_skills:
            skill_list = ", ".join(matching_skills[:3])
            reasons.append(f"Strong skill match: {skill_list}")
        elif skills_score > 0.4:
            reasons.append("Partial skill match with this position")
        
        if location_score == 1.0:
            reasons.append("Perfect location match or remote position")
        elif location_score > 0.7:
            reasons.append("Good location proximity")
        
        if experience_score > 0.8:
            reasons.append("Your experience level aligns well")
        elif experience_score < 0.5:
            reasons.append("May require additional experience")
        
        if salary_score > 0.8:
            reasons.append("Salary range matches your expectations")
        
        return reasons if reasons else ["General match based on profile"]
    
    def _generate_recommendations(
        self,
        missing_skills: List[str],
        experience_score: float
    ) -> List[str]:
        recommendations = []
        
        if missing_skills:
            skills_list = ", ".join(missing_skills[:3])
            recommendations.append(
                f"Consider highlighting transferable skills related to: {skills_list}"
            )
        
        if experience_score < 0.6:
            recommendations.append(
                "Emphasize relevant projects and achievements in your application"
            )
        
        return recommendations
    
    async def score_jobs(
        self,
        user: Union[User, Dict],  # Can be dict or User model
        jobs: List[JobResponse]
    ) -> List[JobResponse]:
        scored_jobs = []
        
        for job in jobs:
            score, match = await self.calculate_match_score(user, job)
            job.match_score = score
            job.relevance_score = match.relevance_score
            scored_jobs.append(job)
        
        scored_jobs.sort(key=lambda j: j.match_score or 0, reverse=True)
        
        return scored_jobs
    
    async def get_matched_jobs(
        self,
        user: Union[User, Dict],  # Can be dict or User model
        db,
        limit: int = 20
    ) -> List[JobResponse]:
        from app.services.job_service import get_job_service
        
        job_service = get_job_service(db)
        
        # Handle both dict and User model for location
        user_location = user.get('location') if isinstance(user, dict) else user.location
        
        result = await job_service.search_jobs(
            query=None,
            location=user_location,
            filters=None,
            page=1,
            size=limit * 2
        )
        
        jobs = result.get("jobs", [])
        scored_jobs = await self.score_jobs(user, jobs)
        
        return scored_jobs[:limit]


matching_service = MatchingService()