# backend/app/integrations/openai_client.py
"""
OpenAI Client for CV parsing and content generation
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from openai import AsyncOpenAI
import logging
from app.core.config import settings
from fastapi import HTTPException


logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured - using mock responses")
            self.client = None
        else:
            try:
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                logger.warning("Falling back to mock responses")
                self.client = None
        
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    async def parse_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Parse CV text and extract structured information using OpenAI
        """
        if not self.client:
            raise HTTPException(
                status_code=503, 
                detail="CV parsing service unavailable. Please contact support."
            )

        system_prompt = """
        You are an expert CV/Resume parser. Extract structured information from the provided CV text.
        Return ONLY a valid JSON object with the following structure:

        {
            "personal_info": {
                "name": "Full name or null",
                "email": "email@example.com or null", 
                "phone": "phone number or null",
                "location": "City, State/Country or null",
                "linkedin": "LinkedIn URL or null",
                "github": "GitHub URL or null",
                "portfolio": "Portfolio URL or null"
            },
            "professional_summary": "Brief professional summary or null",
            "skills": {
                "technical": ["list of technical skills"],
                "soft": ["list of soft skills"], 
                "languages": ["programming/spoken languages"]
            },
            "experience": [
                {
                    "title": "Job title",
                    "company": "Company name",
                    "location": "Location",
                    "start_date": "YYYY-MM or YYYY or null",
                    "end_date": "YYYY-MM or YYYY or Present or null",
                    "duration": "Duration string or null",
                    "description": "Job description",
                    "achievements": ["list of key achievements"]
                }
            ],
            "education": [
                {
                    "degree": "Degree name",
                    "institution": "Institution name",
                    "location": "Location or null",
                    "graduation_date": "YYYY or YYYY-MM or null",
                    "gpa": "GPA if mentioned or null",
                    "field_of_study": "Major/field or null"
                }
            ],
            "certifications": [
                {
                    "name": "Certification name",
                    "issuer": "Issuing organization",
                    "date": "Issue date or null",
                    "expiry": "Expiry date or null",
                    "credential_id": "ID if available or null"
                }
            ],
            "projects": [
                {
                    "name": "Project name",
                    "description": "Project description",
                    "technologies": ["list of technologies used"],
                    "duration": "Duration or null",
                    "url": "Project URL or null"
                }
            ],
            "awards": ["list of awards and honors"],
            "publications": ["list of publications"],
            "volunteer_work": [
                {
                    "organization": "Organization name",
                    "role": "Role/Position",
                    "duration": "Duration or null",
                    "description": "Description"
                }
            ]
        }

        Extract as much information as possible. If a field is not found, use null or empty array.
        Be thorough but accurate. Do not make up information.
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this CV:\n\n{cv_text}"}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Remove any markdown formatting
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                
                parsed_data = json.loads(content)
                return parsed_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {content}")
                return self._get_mock_cv_data()

        except Exception as e:
            logger.error(f"OpenAI API error during CV parsing: {e}")
            return self._get_mock_cv_data()

    async def customize_cv_for_job(self, cv_data: Dict[str, Any], job_description: str, user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Customize CV content for a specific job using OpenAI
        """
        if not self.client:
            return cv_data  # Return original CV data if no OpenAI client

        system_prompt = """
        You are an expert CV customization specialist. Given a CV and job description, 
        customize the CV to highlight the most relevant skills, experience, and achievements 
        for the specific job. Return a JSON object with the same structure as the input CV
        but with optimized content.

        Focus on:
        1. Reordering and emphasizing relevant skills
        2. Highlighting matching experience and achievements
        3. Adjusting professional summary to match job requirements
        4. Optimizing keywords for ATS systems
        5. Maintaining truthfulness - do not add false information
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"CV Data: {json.dumps(cv_data)}\n\nJob Description: {job_description}"}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3  # Lower temperature for consistency
            )

            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            customized_cv = json.loads(content)
            return customized_cv

        except Exception as e:
            logger.error(f"Error customizing CV: {e}")
            return cv_data  # Return original data on error

    async def generate_cover_letter(self, cv_data: Dict[str, Any], job_description: str, company_name: str, user_preferences: Dict[str, Any] = None) -> str:
        """
        Generate a personalized cover letter using OpenAI
        """
        if not self.client:
            return self._get_mock_cover_letter(company_name)

        tone = "professional"
        if user_preferences and "cover_letter_tone" in user_preferences:
            tone = user_preferences["cover_letter_tone"]

        system_prompt = f"""
        You are an expert cover letter writer. Generate a compelling, personalized cover letter 
        based on the candidate's CV data and the job description. 

        Requirements:
        1. Use a {tone} tone
        2. Keep it concise (3-4 paragraphs)
        3. Highlight relevant experience and skills
        4. Show enthusiasm for the specific role and company
        5. Include a strong opening and closing
        6. Make it ATS-friendly
        7. Personalize it for the company and role

        Format as a professional business letter without placeholder brackets.
        """

        cv_summary = {
            "name": cv_data.get("personal_info", {}).get("name", "Candidate"),
            "summary": cv_data.get("professional_summary", ""),
            "key_skills": cv_data.get("skills", {}).get("technical", [])[:5],
            "recent_experience": cv_data.get("experience", [])[:2] if cv_data.get("experience") else []
        }

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"CV Summary: {json.dumps(cv_summary)}\n\nJob Description: {job_description}\n\nCompany: {company_name}"}
                ],
                max_tokens=800,
                temperature=0.7
            )

            cover_letter = response.choices[0].message.content.strip()
            return cover_letter

        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return self._get_mock_cover_letter(company_name)

    async def generate_structured_response(self, system_prompt: str, user_prompt: str, model: str = None) -> str:
        """
        Generic method for structured AI responses
        """
        if not self.client:
            return "{\"error\": \"OpenAI client not configured\"}"

        try:
            response = await self.client.chat.completions.create(
                model=model or self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 3000) -> Dict[str, Any]:
        """
        Generic method for chat completions with OpenAI
        """
        if not self.client:
            logger.warning("OpenAI client not configured - returning empty response")
            return {
                "content": "",
                "error": "OpenAI client not configured"
            }

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return {
                "content": response.choices[0].message.content.strip(),
                "metadata": {
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
                    } if response.usage else {}
                }
            }

        except Exception as e:
            logger.error(f"OpenAI chat completion error: {e}")
            return {
                "content": "",
                "error": str(e)
            }

    def _get_mock_cv_data(self) -> Dict[str, Any]:
        """
        Return mock CV data when OpenAI is not available
        """
        return {
            "personal_info": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "+1-555-0123",
                "location": "San Francisco, CA",
                "linkedin": None,
                "github": None,
                "portfolio": None
            },
            "professional_summary": "Experienced software engineer with expertise in full-stack development",
            "skills": {
                "technical": ["Python", "JavaScript", "React", "Node.js", "MongoDB", "AWS"],
                "soft": ["Leadership", "Communication", "Problem Solving"],
                "languages": ["English (Native)", "Spanish (Conversational)"]
            },
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "location": "San Francisco, CA",
                    "start_date": "2020-01",
                    "end_date": "Present",
                    "duration": "3+ years",
                    "description": "Led development of scalable web applications using modern technologies",
                    "achievements": ["Improved system performance by 40%", "Led team of 5 developers"]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Computer Science",
                    "institution": "University of California",
                    "location": "Berkeley, CA",
                    "graduation_date": "2020",
                    "gpa": None,
                    "field_of_study": "Computer Science"
                }
            ],
            "certifications": [],
            "projects": [],
            "awards": [],
            "publications": [],
            "volunteer_work": []
        }

    def _get_mock_cover_letter(self, company_name: str) -> str:
        """
        Return mock cover letter when OpenAI is not available
        """
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the software engineering position at {company_name}. With over 3 years of experience in full-stack development and a proven track record of delivering scalable solutions, I am confident that I would be a valuable addition to your team.

In my current role as Senior Software Engineer at Tech Corp, I have successfully led the development of multiple web applications using Python, JavaScript, and cloud technologies. I have consistently improved system performance and collaborated effectively with cross-functional teams to deliver high-quality products on time.

I am particularly excited about the opportunity to contribute to {company_name}'s mission and would welcome the chance to discuss how my technical expertise and passion for innovation can benefit your organization.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
John Doe"""


# Singleton instance
openai_client = OpenAIClient()