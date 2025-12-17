# backend/app/services/cv_customization_service.py
"""
CV Customization Service - Phase 3
Tailors CVs for specific job postings using AI
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from bson import ObjectId

from app.integrations.openai_client import openai_client
from app.database import get_database

logger = logging.getLogger(__name__)


class CVCustomizationService:
    """Service for customizing CVs for specific jobs"""
    
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        """Get database instance"""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def customize_cv_for_job(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any],
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Customizing CV for job: {job_data.get('title', 'Unknown')}")
            logger.debug(f"Input cv_data: {cv_data}")
            logger.debug(f"Input job_data: {job_data}")
            logger.debug(f"User preferences: {user_preferences}")
            
            # Build customization prompt
            prompt = self._build_customization_prompt(cv_data, job_data, user_preferences)
            logger.debug(f"Generated prompt: {prompt}")
            
            # Call OpenAI for customization
            logger.debug("Calling OpenAI chat completion")
            customized_content = await openai_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert CV writer and career consultant specializing in ATS optimization and job matching."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=3000
            )
            logger.debug(f"OpenAI response: {customized_content}")
            
            if not customized_content:
                logger.error("Empty response from OpenAI")
                return {
                    "success": False,
                    "error": "Empty response from OpenAI",
                    "customized_cv": cv_data
                }
            
            # Parse and structure the customized CV
            logger.debug("Parsing customized CV")
            customized_cv = await self._parse_customized_cv(
                customized_content,
                cv_data,
                job_data
            )
            
            # Calculate match score
            logger.debug("Calculating match score")
            match_score = await self._calculate_match_score(customized_cv, job_data)
            
            return {
                "success": True,
                "customized_cv": customized_cv,
                "job_match_score": match_score
            }
            
        except Exception as e:
            logger.error(f"CV customization failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "customized_cv": cv_data
            }
    
    def _build_customization_prompt(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any],
        user_preferences: Optional[Dict] = None
    ) -> str:
        """Build AI prompt for CV customization"""
        
        job_title = job_data.get("title", "")
        company = job_data.get("company_name", "")
        description = job_data.get("description", "")
        requirements = job_data.get("requirements", [])
        
        # Handle requirements which can be list of strings or list of dicts
        req_list = []
        if requirements and isinstance(requirements, list):
            for r in requirements:
                if isinstance(r, dict):
                     req_list.append(r.get("requirement", ""))
                else:
                     req_list.append(str(r))
        
        req_str = ', '.join(req_list[:10]) if req_list else 'Not specified'

        prompt = f"""
Customize this CV for a {job_title} position at {company}.

JOB DETAILS:
Title: {job_title}
Company: {company}
Description: {description[:1000]}
Key Requirements: {req_str}

CURRENT CV DATA:
{self._format_cv_for_prompt(cv_data)}

CUSTOMIZATION REQUIREMENTS:
1. Reorder and highlight experiences most relevant to this role
2. Emphasize skills that match the job requirements
3. Use keywords from the job description for ATS optimization
4. Maintain truthfulness - only reframe, don't fabricate
5. Keep the CV concise and impactful (1-2 pages)
6. Tailor the professional summary to this specific role

Please provide a customized CV in the following JSON structure:
{{
    "professional_summary": "Tailored summary...",
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "duration": "Start - End",
            "highlights": ["Achievement 1", "Achievement 2"],
            "relevance_score": 0-10
        }}
    ],
    "skills": {{
        "technical": ["skill1", "skill2"],
        "soft": ["skill1", "skill2"]
    }},
    "education": [...],
    "certifications": [...],
    "ats_keywords": ["keyword1", "keyword2"]
}}
"""
        return prompt
    
    def _format_cv_for_prompt(self, cv_data: Dict[str, Any]) -> str:
        """Format CV data for AI prompt"""
        sections = []
        
        if cv_data.get("personal_info"):
            sections.append(f"Name: {cv_data['personal_info'].get('name', 'N/A')}")
        
        if cv_data.get("professional_summary"):
            sections.append(f"Summary: {cv_data['professional_summary']}")
        
        if cv_data.get("experience"):
            exp_text = "Experience:\n"
            for exp in cv_data["experience"][:5]:  # Limit to 5 most recent
                exp_text += f"- {exp.get('title')} at {exp.get('company')} ({exp.get('duration')})\n"
            sections.append(exp_text)
        
        if cv_data.get("skills"):
            skills = cv_data["skills"]
            if isinstance(skills, list):
                sections.append(f"Skills: {', '.join(skills[:20])}")
            else:
                logger.error(f"Invalid skills type: {type(skills)}, value: {skills}")
                sections.append("Skills: Not available")
        
        if cv_data.get("education"):
            edu_text = "Education:\n"
            for edu in cv_data["education"]:
                edu_text += f"- {edu.get('degree')} from {edu.get('institution')}\n"
            sections.append(edu_text)
        
        return "\n\n".join(sections)
    
    async def _parse_customized_cv(
        self,
        ai_response: str,
        original_cv: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            import json
            
            logger.debug(f"Raw AI response: {ai_response}")
            
            # Try to extract JSON from response
            start_idx = ai_response.find("{")
            end_idx = ai_response.rfind("}") + 1
            logger.debug(f"JSON start_idx: {start_idx}, end_idx: {end_idx}")
            
            if start_idx < 0 or end_idx <= start_idx:
                logger.warning("No valid JSON found in AI response, using original CV")
                return original_cv
            
            json_str = ai_response[start_idx:end_idx]
            logger.debug(f"Extracted JSON string: {json_str}")
            
            try:
                customized_data = json.loads(json_str)
                logger.debug(f"Parsed customized_data: {customized_data}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in AI response: {str(e)}")
                return original_cv
            
            # Validate customized_data is a dict
            if not isinstance(customized_data, dict):
                logger.error(f"Parsed AI response is not a dict: {type(customized_data)}")
                return original_cv
            
            # Sanitize customized_data to prevent slice objects or invalid types
            def sanitize_dict(d):
                if isinstance(d, dict):
                    return {k: sanitize_dict(v) for k, v in d.items()}
                elif isinstance(d, list):
                    return [sanitize_dict(v) for v in d]
                elif isinstance(d, slice):  # Explicitly catch slice objects
                    logger.error(f"Found slice object in AI response: {d}")
                    return str(d)  # Convert to string
                return d
            
            customized_data = sanitize_dict(customized_data)
            logger.debug(f"Sanitized customized_data: {customized_data}")
            
            # Merge with original data, preserving contact info
            result = {
                **original_cv,
                **customized_data,
                "personal_info": original_cv.get("personal_info", {}),
                "customization_metadata": {
                    "job_id": job_data.get("_id"),
                    "job_title": job_data.get("title"),
                    "customized_at": datetime.utcnow()
                }
            }
            logger.debug(f"Final customized CV: {result}")
            return result
                
        except Exception as e:
            logger.error(f"Failed to parse customized CV: {str(e)}", exc_info=True)
            return original_cv
    
    async def _calculate_match_score(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> float:
        """Calculate how well the CV matches the job"""
        try:
            # Simple skill-based matching (since we have raw dicts, not models)
            cv_skills = set()
            if cv_data.get("skills"):
                skills = cv_data["skills"]
                if isinstance(skills, dict):
                    # Flatten categorized skills
                    for skill_list in skills.values():
                        if isinstance(skill_list, list):
                            cv_skills.update(s.lower() for s in skill_list)
                elif isinstance(skills, list):
                    cv_skills.update(s.lower() for s in skills)
            
            job_skills = set()
            if job_data.get("skills_required"):
                job_skills = set(s.lower() for s in job_data["skills_required"])
            elif job_data.get("requirements"):
                # Extract skills from requirements if available
                reqs = job_data["requirements"][:10]
                extracted_reqs = []
                for r in reqs:
                    if isinstance(r, dict):
                         extracted_reqs.append(r.get("requirement", ""))
                    else:
                         extracted_reqs.append(str(r))
                job_skills = set(s.lower() for s in extracted_reqs)
            
            # Calculate Jaccard similarity
            if not job_skills:
                return 0.75  # Default score if no job skills
            
            if not cv_skills:
                return 0.5
            
            intersection = len(cv_skills & job_skills)
            union = len(cv_skills | job_skills)
            
            score = intersection / union if union > 0 else 0.5
            
            # Boost score slightly for having any matches
            if intersection > 0:
                score = min(1.0, score + 0.2)
            
            return round(score, 2)
            
        except Exception as e:
            logger.warning(f"Match score calculation failed: {e}. Returning default score.")
            return 0.75  # Default 75% match
    
    async def generate_multiple_versions(
        self,
        cv_data: Dict[str, Any],
        jobs: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Generate customized CVs for multiple jobs in batch
        
        Args:
            cv_data: Original CV data
            jobs: List of job postings
            user_id: User ID for tracking
            
        Returns:
            List of customized CV results
        """
        results = []
        db = await self._get_db()
        
        for job in jobs:
            try:
                # Customize CV for this job
                result = await self.customize_cv_for_job(cv_data, job)
                
                if result["success"]:
                    # Store generated version
                    doc_id = await self._store_generated_cv(
                        user_id=user_id,
                        job_id=str(job.get("_id")),
                        customized_cv=result["customized_cv"],
                        match_score=result["job_match_score"]
                    )
                    
                    result["document_id"] = doc_id
                
                results.append({
                    "job_id": str(job.get("_id")),
                    "job_title": job.get("title"),
                    **result
                })
                
            except Exception as e:
                logger.error(f"Failed to customize CV for job {job.get('_id')}: {e}")
                results.append({
                    "job_id": str(job.get("_id")),
                    "job_title": job.get("title"),
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _store_generated_cv(
        self,
        user_id: str,
        job_id: str,
        customized_cv: Dict[str, Any],
        match_score: float
    ) -> str:
        """Store generated CV in database"""
        db = await self._get_db()
        
        doc = {
            "user_id": user_id,
            "job_id": job_id,
            "type": "customized_cv",
            "content": customized_cv,
            "match_score": match_score,
            "generated_at": datetime.utcnow(),
            "status": "generated"
        }
        
        result = await db.generated_documents.insert_one(doc)
        return str(result.inserted_id)
    
    async def get_generated_cv(
        self,
        document_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a generated CV"""
        db = await self._get_db()
        
        doc = await db.generated_documents.find_one({
            "_id": ObjectId(document_id),
            "user_id": user_id,
            "type": "customized_cv"
        })
        
        if doc:
            doc["_id"] = str(doc["_id"])
        
        return doc


# Create singleton instance
cv_customization_service = CVCustomizationService()