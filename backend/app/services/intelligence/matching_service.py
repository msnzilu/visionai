import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.config import settings
import openai

logger = logging.getLogger(__name__)

class MatchingService:
    """Service for job matching and role suggestions"""

    def __init__(self, db=None):
        self.db = db

    async def get_suggested_roles(self, user_cv: Dict, limit: int = 8) -> List[Dict]:
        """
        Get suggested job roles based on CV analysis
        """
        if not user_cv:
            return []

        # Extract relevant info
        skills = user_cv.get("skills", {})
        if isinstance(skills, dict):
            all_skills = skills.get("technical", []) + skills.get("soft", [])
        else:
            all_skills = skills if isinstance(skills, list) else []
        
        experience = user_cv.get("experience", [])
        current_role = None
        if experience and len(experience) > 0:
            current_role = experience[0].get("title")
        
        suggested_roles = []
        
        # 1. Add current/recent role if exists
        if current_role:
            suggested_roles.append({
                "title": current_role,
                "reason": "Your current role",
                "match_type": "current"
            })
        
        # 2. Add previous roles (unique)
        seen_roles = {current_role.lower() if current_role else ""}
        for exp in experience[1:4]:  # Next 3 previous roles
            title = exp.get("title")
            if title and title.lower() not in seen_roles:
                suggested_roles.append({
                    "title": title,
                    "reason": "Previous experience",
                    "match_type": "experience"
                })
                seen_roles.add(title.lower())
        
        # 3. Suggest roles based on skills
        skill_based_roles = self._suggest_roles_from_skills(all_skills)
        for role in skill_based_roles:
            if role["title"].lower() not in seen_roles:
                suggested_roles.append(role)
                seen_roles.add(role["title"].lower())
        
        return suggested_roles[:limit]

    def _suggest_roles_from_skills(self, skills: list) -> list:
        """
        Map skills to suggested job roles
        """
        skills_lower = [s.lower() for s in skills if isinstance(s, str)]
        suggested = []
        
        # Role mappings based on skill combinations
        role_mappings = {
            "Full Stack Developer": ["javascript", "python", "react", "node", "sql", "html", "css"],
            "Frontend Developer": ["react", "vue", "angular", "javascript", "typescript", "css", "html"],
            "Backend Developer": ["python", "java", "node", "sql", "api", "django", "flask", "spring"],
            "Data Scientist": ["python", "machine learning", "pandas", "numpy", "tensorflow", "data analysis"],
            "Data Engineer": ["python", "sql", "spark", "etl", "airflow", "data pipeline"],
            "DevOps Engineer": ["docker", "kubernetes", "aws", "azure", "ci/cd", "terraform", "jenkins"],
            "Cloud Engineer": ["aws", "azure", "gcp", "cloud", "terraform", "kubernetes"],
            "Mobile Developer": ["android", "ios", "react native", "flutter", "swift", "kotlin"],
            "Product Manager": ["product management", "agile", "scrum", "roadmap", "stakeholder"],
            "Project Manager": ["project management", "agile", "scrum", "jira", "planning"],
            "UI/UX Designer": ["figma", "sketch", "user experience", "user interface", "wireframe"],
            "QA Engineer": ["testing", "selenium", "qa", "automation", "quality assurance"],
            "Machine Learning Engineer": ["machine learning", "tensorflow", "pytorch", "deep learning", "nlp"],
            "Security Engineer": ["security", "penetration", "cybersecurity", "vulnerability", "compliance"],
            "Software Engineer": ["programming", "software development", "coding", "algorithms"]
        }
        
        for role, required_skills in role_mappings.items():
            matching_skills = [s for s in required_skills if any(s in skill for skill in skills_lower)]
            match_ratio = len(matching_skills) / len(required_skills) if required_skills else 0
            
            if match_ratio >= 0.3:  # At least 30% skill match
                suggested.append({
                    "title": role,
                    "reason": f"Matches {len(matching_skills)} of your skills",
                    "match_type": "skills",
                    "match_score": round(match_ratio * 100)
                })
        
        # Sort by match score
        suggested.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return suggested[:5]

    async def calculate_match_score(self, user_cv: Dict, job: Dict, use_ai: bool = True) -> float:
        """
        Calculate match score between user CV and job
        """
        if use_ai and settings.OPENAI_API_KEY:
            return await self._calculate_ai_match_score(user_cv, job)
        else:
            return self._calculate_simple_match_score(user_cv, job)

    async def _calculate_ai_match_score(self, user_cv: Dict, job: Dict) -> float:
        """
        Use OpenAI to calculate match score
        """
        try:
            openai.api_key = settings.OPENAI_API_KEY
            
            # Extract key info
            cv_skills = user_cv.get("skills", [])
            if isinstance(cv_skills, dict):
                cv_skills = cv_skills.get("technical", []) + cv_skills.get("soft", [])
                
            cv_experience = len(user_cv.get("experience", []))
            
            job_title = job.get("title", "")
            job_requirements = job.get("requirements", "")
            if isinstance(job_requirements, list):
                job_requirements = " ".join(job_requirements)
            
            prompt = f"""
            Analyze the match between this candidate and job. Return ONLY a number between 0.0 and 1.0.
            
            Candidate Skills: {', '.join(cv_skills[:15] if cv_skills else [])}
            Candidate Experience: {cv_experience} entries
            
            Job Title: {job_title}
            Job Requirements: {job_requirements[:1000]}
            
            Match Score (0.0-1.0):
            """
            
            response = await openai.ChatCompletion.acreate(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.3
            )
            
            score_text = response.choices[0].message.content.strip()
            # Clean up response to ensure float
            import re
            match = re.search(r"0\.\d+|1\.0|0|1", score_text)
            if match:
                score = float(match.group(0))
                return min(max(score, 0.0), 1.0)
            return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating AI match score: {e}")
            return self._calculate_simple_match_score(user_cv, job)

    def _calculate_simple_match_score(self, user_cv: Dict, job: Dict) -> float:
        """
        Simple keyword-based match score
        """
        cv_skills = user_cv.get("skills", [])
        if isinstance(cv_skills, dict):
            cv_skills = cv_skills.get("technical", []) + cv_skills.get("soft", [])
        
        user_skills = set([s.lower() for s in cv_skills if isinstance(s, str)])
        
        # Extract skills from job
        job_description = str(job.get("description", ""))
        job_requirements = job.get("requirements", "")
        if isinstance(job_requirements, list):
            job_requirements = " ".join(job_requirements)
        
        job_text = (job_description + " " + str(job_requirements)).lower()
        
        # Count skill matches
        matches = sum(1 for skill in user_skills if skill in job_text)
        total_skills = len(user_skills)
        
        if total_skills == 0:
            return 0.5
        
        score = matches / total_skills
        
        # Bonus for title match
        job_title = job.get("title", "").lower()
        current_role = ""
        experience = user_cv.get("experience", [])
        if experience:
             current_role = experience[0].get("title", "").lower()
        
        if current_role and (current_role in job_title or job_title in current_role):
            score += 0.2
            
        return min(max(score, 0.0), 1.0)

    async def find_matching_jobs(self, user_id: str, cv_data: Dict, limit: int = 5, exclude_job_ids: List[ObjectId] = None, days_lookback: int = 7) -> List[Dict]:
        """
        Find best matching jobs for a user
        """
        if self.db is None:
             logger.error("Database connection required for finding matching jobs")
             return []

        # Get jobs user hasn't applied to
        applied_job_ids = await self.db.applications.distinct("job_id", {"user_id": user_id})
        exclude_ids = [ObjectId(jid) for jid in applied_job_ids if ObjectId.is_valid(jid)]
        
        # Add explicitly excluded jobs (e.g. from previous emails)
        if exclude_job_ids:
            exclude_ids.extend(exclude_job_ids)
        
        # Remove duplicates from exclusions
        exclude_ids = list(set(exclude_ids))

        # Get recent jobs
        start_date = datetime.utcnow() - timedelta(days=days_lookback)
        
        # Strategy: 
        # 1. Get jobs matching suggested roles first (more relevant)
        # 2. Fill with recent jobs
        
        suggested_roles = await self.get_suggested_roles(cv_data, limit=3)
        role_queries = [{"title": {"$regex": role["title"], "$options": "i"}} for role in suggested_roles]
        
        candidate_jobs = []
        
        if role_queries:
            candidate_jobs = await self.db.jobs.find({
                "_id": {"$nin": exclude_ids},
                "is_active": True,
                "created_at": {"$gte": start_date},
                "$or": role_queries
            }).limit(limit * 3).to_list(length=limit * 3)
            
        # If not enough, get generic recent jobs
        if len(candidate_jobs) < limit * 2:
            current_ids = [j["_id"] for j in candidate_jobs]
            more_jobs = await self.db.jobs.find({
                "_id": {"$nin": exclude_ids + current_ids},
                "is_active": True,
                "created_at": {"$gte": start_date}
            }).limit(limit * 2).to_list(length=limit * 2)
            candidate_jobs.extend(more_jobs)
            
        # Score jobs
        job_scores = []
        for job in candidate_jobs:
            score = await self.calculate_match_score(cv_data, job, use_ai=False) # Use simple score for speed in list
            job_scores.append((job, score))
            
        # Sort and return top matches
        job_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {**job, "match_score": score} 
            for job, score in job_scores[:limit]
        ]

# Global instance
matching_service = MatchingService()