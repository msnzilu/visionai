# backend/app/services/ai_service.py
"""
AI Service - High-level service for AI-powered features
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.integrations.openai_client import openai_client
from app.models.user import User
from app.database import get_database

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.openai_client = openai_client

    async def process_cv_with_ai(self, cv_text: str, user_id: str) -> Dict[str, Any]:
        """
        Process CV text using AI and store results
        """
        try:
            # Parse CV using OpenAI
            parsed_cv = await self.openai_client.parse_cv(cv_text)
            
            # Add processing metadata
            processing_metadata = {
                "processed_at": datetime.utcnow(),
                "processing_version": "1.0",
                "user_id": user_id,
                "text_length": len(cv_text),
                "ai_model": "gpt-4"
            }
            
            # Combine parsed data with metadata
            result = {
                "cv_data": parsed_cv,
                "metadata": processing_metadata,
                "status": "completed"
            }
            
            # Update user profile with CV data
            await self._update_user_profile_from_cv(user_id, parsed_cv)
            
            logger.info(f"Successfully processed CV for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing CV with AI: {e}")
            return {
                "cv_data": {},
                "metadata": {
                    "processed_at": datetime.utcnow(),
                    "error": str(e),
                    "status": "failed"
                },
                "status": "failed"
            }

    async def customize_cv_for_job(self, cv_data: Dict[str, Any], job_description: str, 
                                 company_name: str, user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Customize CV for a specific job posting
        """
        try:
            customized_cv = await self.openai_client.customize_cv_for_job(
                cv_data=cv_data,
                job_description=job_description,
                user_preferences=user_preferences
            )
            
            # Add customization metadata
            customization_metadata = {
                "customized_at": datetime.utcnow(),
                "target_company": company_name,
                "job_description_length": len(job_description),
                "customization_version": "1.0"
            }
            
            return {
                "customized_cv": customized_cv,
                "metadata": customization_metadata,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error customizing CV: {e}")
            return {
                "customized_cv": cv_data,  # Return original on error
                "metadata": {"error": str(e), "status": "failed"},
                "status": "failed"
            }

    async def generate_cover_letter(self, cv_data: Dict[str, Any], job_description: str,
                                  company_name: str, job_title: str = "", 
                                  user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate personalized cover letter
        """
        try:
            cover_letter = await self.openai_client.generate_cover_letter(
                cv_data=cv_data,
                job_description=job_description,
                company_name=company_name,
                user_preferences=user_preferences
            )
            
            # Add generation metadata
            generation_metadata = {
                "generated_at": datetime.utcnow(),
                "target_company": company_name,
                "job_title": job_title,
                "word_count": len(cover_letter.split()),
                "character_count": len(cover_letter),
                "tone": user_preferences.get("cover_letter_tone", "professional") if user_preferences else "professional"
            }
            
            return {
                "cover_letter": cover_letter,
                "metadata": generation_metadata,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return {
                "cover_letter": self._get_fallback_cover_letter(company_name, job_title),
                "metadata": {"error": str(e), "status": "failed"},
                "status": "failed"
            }

    async def analyze_job_match(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Analyze how well a CV matches a job description
        """
        try:
            system_prompt = """
            Analyze how well this candidate's CV matches the job description.
            Return a JSON object with:
            {
                "match_score": float (0-100),
                "matching_skills": ["list of matching skills"],
                "missing_skills": ["list of missing key skills"],
                "experience_match": {
                    "score": float (0-100),
                    "relevant_roles": ["list of relevant past roles"],
                    "experience_gap": "description of gaps if any"
                },
                "education_match": {
                    "score": float (0-100),
                    "relevant_education": ["relevant degrees/certifications"]
                },
                "recommendations": ["list of improvement suggestions"],
                "strengths": ["list of candidate strengths for this role"],
                "overall_assessment": "brief overall assessment"
            }
            """
            
            user_prompt = f"CV Data: {cv_data}\n\nJob Description: {job_description}"
            
            response = await self.openai_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            import json
            analysis = json.loads(response)
            
            return {
                "analysis": analysis,
                "analyzed_at": datetime.utcnow(),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing job match: {e}")
            return {
                "analysis": {
                    "match_score": 50.0,
                    "overall_assessment": "Unable to perform detailed analysis"
                },
                "error": str(e),
                "status": "failed"
            }

    async def enhance_cv_data(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance CV data with additional AI-powered insights
        """
        try:
            # Extract skills and suggest improvements
            enhanced_data = cv_data.copy()
            
            # Add skill categorization
            if "skills" in enhanced_data:
                enhanced_data["skills"]["categorized"] = await self._categorize_skills(
                    enhanced_data["skills"].get("technical", [])
                )
            
            # Add experience insights
            if "experience" in enhanced_data:
                enhanced_data["experience_insights"] = await self._analyze_experience_progression(
                    enhanced_data["experience"]
                )
            
            return {
                "enhanced_cv": enhanced_data,
                "enhanced_at": datetime.utcnow(),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error enhancing CV data: {e}")
            return {
                "enhanced_cv": cv_data,
                "error": str(e),
                "status": "failed"
            }

    async def _update_user_profile_from_cv(self, user_id: str, cv_data: Dict[str, Any]) -> None:
        """
        Update user profile with extracted CV information
        """
        try:
            db = await get_database()
            
            # Extract key information for profile update
            profile_updates = {}
            
            if "personal_info" in cv_data:
                personal_info = cv_data["personal_info"]
                profile_updates["profile.personal_info.linkedin_url"] = personal_info.get("linkedin")
                profile_updates["profile.personal_info.github_url"] = personal_info.get("github")
                profile_updates["profile.personal_info.portfolio_url"] = personal_info.get("portfolio")
                
                if personal_info.get("location"):
                    # Simple location parsing - can be enhanced
                    location_parts = personal_info["location"].split(",")
                    if len(location_parts) >= 2:
                        profile_updates["profile.personal_info.city"] = location_parts[0].strip()
                        profile_updates["profile.personal_info.state"] = location_parts[1].strip()
            
            if "skills" in cv_data:
                all_skills = []
                skills_data = cv_data["skills"]
                all_skills.extend(skills_data.get("technical", []))
                all_skills.extend(skills_data.get("soft", []))
                profile_updates["profile.skills"] = all_skills[:20]  # Limit to top 20 skills
            
            if "professional_summary" in cv_data and cv_data["professional_summary"]:
                profile_updates["profile.bio"] = cv_data["professional_summary"]
            
            # Calculate experience years
            if "experience" in cv_data:
                total_years = self._calculate_total_experience(cv_data["experience"])
                profile_updates["profile.experience_years"] = total_years
            
            # Update database
            if profile_updates:
                from bson import ObjectId
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": profile_updates}
                )
                logger.info(f"Updated user profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user profile from CV: {e}")

    async def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills into different types
        """
        # Simple categorization - can be enhanced with AI
        categories = {
            "programming_languages": [],
            "frameworks": [],
            "databases": [],
            "cloud_platforms": [],
            "tools": [],
            "other": []
        }
        
        programming_languages = ["python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust", "swift"]
        frameworks = ["react", "angular", "vue", "django", "flask", "express", "spring", "laravel"]
        databases = ["mongodb", "mysql", "postgresql", "redis", "elasticsearch", "cassandra"]
        cloud_platforms = ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"]
        
        for skill in skills:
            skill_lower = skill.lower()
            if any(lang in skill_lower for lang in programming_languages):
                categories["programming_languages"].append(skill)
            elif any(fw in skill_lower for fw in frameworks):
                categories["frameworks"].append(skill)
            elif any(db in skill_lower for db in databases):
                categories["databases"].append(skill)
            elif any(cloud in skill_lower for cloud in cloud_platforms):
                categories["cloud_platforms"].append(skill)
            else:
                categories["other"].append(skill)
        
        return categories

    async def _analyze_experience_progression(self, experience: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze career progression from experience data
        """
        if not experience:
            return {"progression": "No experience data available"}
        
        # Sort by start date
        sorted_experience = sorted(
            experience, 
            key=lambda x: x.get("start_date", ""), 
            reverse=True
        )
        
        return {
            "total_roles": len(experience),
            "current_role": sorted_experience[0] if sorted_experience else None,
            "career_progression": "ascending" if len(experience) > 1 else "single_role",
            "industries": list(set([exp.get("company", "") for exp in experience if exp.get("company")]))
        }

    def _calculate_total_experience(self, experience: List[Dict[str, Any]]) -> int:
        """
        Calculate total years of experience
        """
        # Simple calculation - can be enhanced
        return len(experience) * 2  # Rough estimate

    def _get_fallback_cover_letter(self, company_name: str, job_title: str) -> str:
        """
        Fallback cover letter when AI generation fails
        """
        return f"""Dear Hiring Manager,

I am writing to express my interest in the {job_title or 'position'} at {company_name}. With my background in software development and proven track record of delivering high-quality solutions, I am confident I would be a valuable addition to your team.

My experience includes full-stack development, working with modern technologies, and collaborating effectively in team environments. I am passionate about creating efficient, scalable solutions and am excited about the opportunity to contribute to {company_name}'s success.

I would welcome the opportunity to discuss how my skills and enthusiasm can benefit your organization. Thank you for considering my application.

Best regards,
[Your Name]"""


# Singleton instance
ai_service = AIService()