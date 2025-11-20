# backend/app/models/job.py
"""
Job-related Pydantic models
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import re

from .common import TimeStampedModel, SoftDeleteModel, Address, ContactInfo, Money, Priority


class JobSource(str, Enum):
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    COMPANY_WEBSITE = "company_website"
    JOB_BOARD = "job_board"
    MANUAL = "manual"
    API = "api"
    SCRAPER = "scraper"


class JobStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FILLED = "filled"
    EXPIRED = "expired"
    DRAFT = "draft"
    PENDING = "pending"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    VOLUNTEER = "volunteer"


class ExperienceLevel(str, Enum):
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class WorkArrangement(str, Enum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FLEXIBLE = "flexible"


class CompanySize(str, Enum):
    STARTUP = "startup"          # 1-10 employees
    SMALL = "small"              # 11-50 employees
    MEDIUM = "medium"            # 51-200 employees
    LARGE = "large"              # 201-1000 employees
    ENTERPRISE = "enterprise"    # 1000+ employees


class Industry(str, Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    CONSULTING = "consulting"
    MEDIA = "media"
    REAL_ESTATE = "real_estate"
    TRANSPORTATION = "transportation"
    ENERGY = "energy"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    OTHER = "other"


# Salary and Benefits Models
class SalaryRange(BaseModel):
    """Salary range model"""
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    currency: str = "USD"
    period: str = "yearly"  # yearly, monthly, weekly, hourly
    is_negotiable: bool = False
    
    @validator('max_amount')
    def validate_salary_range(cls, v, values):
        min_amount = values.get('min_amount')
        if v is not None and min_amount is not None and v < min_amount:
            raise ValueError("Maximum salary must be greater than minimum")
        return v
    
    def __str__(self):
        if self.min_amount and self.max_amount:
            return f"{self.min_amount:,.0f} - {self.max_amount:,.0f} {self.currency}/{self.period}"
        elif self.min_amount:
            return f"{self.min_amount:,.0f}+ {self.currency}/{self.period}"
        elif self.max_amount:
            return f"Up to {self.max_amount:,.0f} {self.currency}/{self.period}"
        else:
            return "Salary not specified"


class JobBenefit(BaseModel):
    """Job benefit model"""
    name: str
    description: Optional[str] = None
    category: str = "general"  # health, financial, time_off, development, perks
    value: Optional[str] = None


class JobRequirement(BaseModel):
    """Job requirement model"""
    requirement: str
    is_required: bool = True
    category: str = "general"  # education, experience, skills, certifications
    priority: Priority = Priority.MEDIUM


# Company Models
class CompanyInfo(BaseModel):
    """Company information model"""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    size: Optional[CompanySize] = None
    industry: Optional[Industry] = None
    founded_year: Optional[int] = Field(None, ge=1800, le=datetime.now().year)
    headquarters: Optional[Address] = None
    contact: Optional[ContactInfo] = None
    social_links: Optional[Dict[str, str]] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    employee_count: Optional[int] = Field(None, ge=0)


# Core Job Models
class JobBase(BaseModel):
    """Base job model with common fields"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    company_name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    employment_type: Optional[EmploymentType] = None
    work_arrangement: Optional[WorkArrangement] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_range: Optional[SalaryRange] = None
    requirements: List[JobRequirement] = []
    benefits: List[JobBenefit] = []
    skills_required: List[str] = []
    skills_preferred: List[str] = []
    application_deadline: Optional[date] = None
    start_date: Optional[date] = None


class JobCreate(JobBase):
    """Model for creating a new job"""
    source: JobSource = JobSource.MANUAL
    external_id: Optional[str] = None
    external_url: Optional[HttpUrl] = None
    company_info: Optional[CompanyInfo] = None
    posted_by: Optional[str] = None  # User ID who posted the job


class JobUpdate(BaseModel):
    """Model for updating an existing job"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    company_name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    employment_type: Optional[EmploymentType] = None
    work_arrangement: Optional[WorkArrangement] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_range: Optional[SalaryRange] = None
    requirements: Optional[List[JobRequirement]] = None
    benefits: Optional[List[JobBenefit]] = None
    skills_required: Optional[List[str]] = None
    skills_preferred: Optional[List[str]] = None
    application_deadline: Optional[date] = None
    start_date: Optional[date] = None
    status: Optional[JobStatus] = None


class Job(JobBase, TimeStampedModel):
    """Complete job model"""
    id: Optional[str] = Field(alias="_id")
    status: JobStatus = JobStatus.ACTIVE
    source: JobSource = JobSource.MANUAL
    external_id: Optional[str] = None
    external_url: Optional[HttpUrl] = None
    company_info: Optional[CompanyInfo] = None
    posted_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    posted_by: Optional[str] = None  # User ID
    
    # Analytics and matching
    view_count: int = 0
    application_count: int = 0
    relevance_score: Optional[float] = Field(None, ge=0, le=1)
    match_score: Optional[float] = Field(None, ge=0, le=1)
    
    # SEO and search
    tags: List[str] = []
    keywords: List[str] = []
    
    # Internal tracking
    is_featured: bool = False
    is_urgent: bool = False
    internal_notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }


class JobResponse(BaseModel):
    """Job response model for API responses"""
    id: str
    title: str
    description: str
    company_name: str
    location: str
    employment_type: Optional[EmploymentType]
    work_arrangement: Optional[WorkArrangement]
    experience_level: Optional[ExperienceLevel]
    salary_range: Optional[SalaryRange]
    requirements: List[JobRequirement] = []  # Add default
    benefits: List[JobBenefit] = []  # Add default
    skills_required: List[str] = []  # Add default
    skills_preferred: List[str] = []  # Add default
    status: JobStatus
    source: JobSource
    external_url: Optional[HttpUrl] = None  # Add default
    company_info: Optional[CompanyInfo] = None  # Add default
    posted_date: Optional[datetime] = None  # Add default
    application_deadline: Optional[date] = None  # Add default
    created_at: datetime
    updated_at: datetime
    relevance_score: Optional[float] = None  # Add default
    match_score: Optional[float] = None  # Add default
    view_count: int = 0  # Add default
    application_count: int = 0  # Add default
    is_featured: bool = False  # Add default ← FIX THIS
    tags: List[str] = []  # Add default ← FIX THIS
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }


# Search and Filter Models
class JobFilter(BaseModel):
    """Job search filter model"""
    location: Optional[str] = None
    radius_miles: Optional[int] = Field(None, ge=1, le=500)
    remote_only: bool = False
    employment_types: List[EmploymentType] = []
    experience_levels: List[ExperienceLevel] = []
    work_arrangements: List[WorkArrangement] = []
    company_sizes: List[CompanySize] = []
    industries: List[Industry] = []
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    keywords: List[str] = []
    skills: List[str] = []
    posted_after: Optional[date] = None
    posted_before: Optional[date] = None
    has_salary: Optional[bool] = None
    is_featured: Optional[bool] = None


class JobSearch(BaseModel):
    """Job search request model"""
    query: Optional[str] = None
    filters: Optional[JobFilter] = None
    location: Optional[str] = None
    radius_miles: int = Field(default=25, ge=1, le=500)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "relevance"  # relevance, date, salary, title, company
    sort_order: str = "desc"  # asc, desc
    user_id: Optional[str] = None  # For personalized results


class JobMatch(BaseModel):
    """Job matching result model"""
    job_id: str
    user_id: str
    match_score: float = Field(..., ge=0, le=1)
    relevance_score: float = Field(..., ge=0, le=1)
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    match_reasons: List[str] = []
    recommendations: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobListResponse(BaseModel):
    """Job list response with pagination"""
    jobs: List[JobResponse]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    filters_applied: Optional[JobFilter] = None
    search_query: Optional[str] = None
    total_time_ms: Optional[float] = None


# Job Analytics Models
class JobStats(BaseModel):
    """Job statistics model"""
    total_jobs: int = 0
    active_jobs: int = 0
    jobs_this_week: int = 0
    jobs_this_month: int = 0
    top_companies: List[Dict[str, Any]] = []
    top_locations: List[Dict[str, Any]] = []
    top_skills: List[Dict[str, Any]] = []
    avg_salary: Optional[float] = None
    salary_distribution: Dict[str, int] = {}
    employment_type_distribution: Dict[str, int] = {}


# Job Scraping Models
class ScrapingConfig(BaseModel):
    """Job scraping configuration"""
    source: JobSource
    base_url: str
    search_params: Dict[str, Any] = {}
    headers: Dict[str, str] = {}
    rate_limit: int = 1  # requests per second
    max_pages: int = 10
    selectors: Dict[str, str] = {}  # CSS selectors for data extraction
    is_active: bool = True


class ScrapingResult(BaseModel):
    """Job scraping result"""
    source: JobSource
    jobs_found: int
    jobs_created: int
    jobs_updated: int
    errors: List[str] = []
    execution_time: float
    last_run: datetime = Field(default_factory=datetime.utcnow)


# Job Application Integration Models
class ApplicationLink(BaseModel):
    """Job application link model"""
    url: HttpUrl
    type: str = "external"  # external, email, phone
    instructions: Optional[str] = None
    auto_fillable: bool = False
    form_fields: List[Dict[str, Any]] = []


class JobAlert(BaseModel):
    """Job alert model"""
    id: Optional[str] = Field(alias="_id")
    user_id: str
    name: str
    search_criteria: JobSearch
    frequency: str = "daily"  # immediate, daily, weekly
    is_active: bool = True
    last_sent: Optional[datetime] = None
    jobs_sent: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


# Export all job-related models
__all__ = [
    "JobSource", "JobStatus", "EmploymentType", "ExperienceLevel", "WorkArrangement",
    "CompanySize", "Industry", "SalaryRange", "JobBenefit", "JobRequirement",
    "CompanyInfo", "JobBase", "JobCreate", "JobUpdate", "Job", "JobResponse",
    "JobFilter", "JobSearch", "JobMatch", "JobListResponse", "JobStats",
    "ScrapingConfig", "ScrapingResult", "ApplicationLink", "JobAlert"
]