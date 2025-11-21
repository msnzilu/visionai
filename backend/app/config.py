"""
Configuration settings for the AI Job Application Platform
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional, Union
import secrets
import os
from pathlib import Path


class Settings(BaseSettings):
    # Project information
    PROJECT_NAME: str = "Visions AI"
    PROJECT_DESCRIPTION: str = "Comprehensive AI-powered job application automation platform"
    PROJECT_VERSION: str = "1.0.0"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    JWT_SECRET_KEY: str = Field(default="dev-jwt-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24

    CORS_ORIGINS: List[str] = [
    "http://localhost",      # Matches your browser origin (port 80 implied)
    "http://localhost:80",
    "http://127.0.0.1",
    "http://172.18.0.1",     # Docker gateway from logs
]

    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    MONGODB_URL: str = Field(default="mongodb://mongo:27017", env="MONGODB_URL")
    DATABASE_NAME: str = Field(default="job_platform", env="DATABASE_NAME")
    
    # Redis (for caching and rate limiting) - Optional for Phase 1
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    
    # External APIs - Made optional for Phase 1
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Stripe - Optional for Phase 1
    STRIPE_SECRET_KEY: str = Field(default="", env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str = Field(default="", env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")
    
    # Email service - Optional for Phase 1
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(default="", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = True

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    FRONTEND_URL: str        # URL to your frontend for verification/reset links
    SUPPORT_EMAIL: str       # Support email for contact in templates
    COMPANY_NAME: str        # Your company/app name for branding in emails


    # Job board APIs - Optional for Phase 1
    INDEED_API_KEY: Optional[str] = Field(default=None, env="INDEED_API_KEY")
    LINKEDIN_API_KEY: Optional[str] = Field(default=None, env="LINKEDIN_API_KEY")
    GLASSDOOR_API_KEY: Optional[str] = Field(default=None, env="GLASSDOOR_API_KEY")
    
    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".doc", ".txt"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    
    # Subscription limits
    FREE_TIER_MONTHLY_ATTEMPTS: int = 1
    FREE_TIER_JOBS_PER_ATTEMPT: int = 3
    
    BASIC_TIER_DAILY_ATTEMPTS: int = 5
    BASIC_TIER_MONTHLY_ATTEMPTS: int = 150
    BASIC_TIER_JOBS_PER_ATTEMPT: int = 10
    BASIC_TIER_PRICE: int = 2000  # $20.00 in cents
    
    PREMIUM_TIER_MONTHLY_ATTEMPTS: int = 200
    PREMIUM_TIER_JOBS_PER_ATTEMPT: int = 10
    PREMIUM_TIER_PRICE: int = 4900  # $49.00 in cents
    
    # Referral system
    REFERRALS_FOR_FREE_ATTEMPT: int = 5
    BASIC_REFERRAL_BONUS: int = 2
    PREMIUM_REFERRAL_BONUS: int = 5
    
    # Browser automation service
    AUTOMATION_SERVICE_URL: str = Field(
        default="http://localhost:3001", 
        env="AUTOMATION_SERVICE_URL"
    )
    AUTOMATION_SERVICE_TOKEN: str = Field(default="dev-automation-token")
    
    # Machine Learning
    ML_MODEL_PATH: str = "ml-models/models/"
    ML_TRAINING_DATA_PATH: str = "ml-models/data/"
    ML_RETRAIN_INTERVAL_DAYS: int = 7
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Background tasks
    CELERY_BROKER_URL: str = Field(
        default="redis://redis:6379/0", 
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://redis:6379/0", 
        env="CELERY_RESULT_BACKEND"
    )
    
    # Webhooks
    WEBHOOK_SECRET: str = Field(default="dev-webhook-secret")

    # Job Board API Keys (Phase 2)
    INDEED_PUBLISHER_ID: str = Field(default="", env="INDEED_PUBLISHER_ID")
    INDEED_API_KEY: Optional[str] = Field(default=None, env="INDEED_API_KEY")
    LINKEDIN_API_KEY: Optional[str] = Field(default=None, env="LINKEDIN_API_KEY")
    GLASSDOOR_API_KEY: Optional[str] = Field(default=None, env="GLASSDOOR_API_KEY")


    # Scraping Configuration (Phase 2)
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    SCRAPER_DELAY_MIN: int = 2
    SCRAPER_DELAY_MAX: int = 5
    SCRAPER_MAX_RETRIES: int = 3

    # Cache Settings (Phase 2)
    CACHE_TTL_DEFAULT: int = 3600  # 1 hour
    CACHE_TTL_JOB_SEARCH: int = 1800  # 30 minutes
    CACHE_TTL_JOB_DETAILS: int = 7200  # 2 hours

    # Job Settings (Phase 2)
    JOB_EXPIRY_DAYS: int = 90
    MAX_JOBS_PER_SEARCH: int = 100

        # Stripe Configuration (Phase 4)
    STRIPE_SECRET_KEY: str = Field(default="", env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str = Field(default="", env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")

    # Stripe Price IDs (create these in Stripe Dashboard)
    STRIPE_BASIC_PRICE_ID: str = Field(default="", env="STRIPE_BASIC_PRICE_ID")
    STRIPE_PREMIUM_PRICE_ID: str = Field(default="", env="STRIPE_PREMIUM_PRICE_ID")

    # Subscription Configuration
    FREE_TIER_MONTHLY_SEARCHES: int = 1
    FREE_TIER_JOBS_PER_SEARCH: int = 3
    FREE_TIER_REFERRALS_FOR_BONUS: int = 5

    BASIC_TIER_MONTHLY_SEARCHES: int = 150
    BASIC_TIER_JOBS_PER_SEARCH: int = 10
    BASIC_TIER_PRICE: int = 2000  # $20.00 in cents
    BASIC_TIER_REFERRAL_BONUS: int = 2

    PREMIUM_TIER_MONTHLY_SEARCHES: int = 200
    PREMIUM_TIER_JOBS_PER_SEARCH: int = 10
    PREMIUM_TIER_PRICE: int = 4900  # $49.00 in cents
    PREMIUM_TIER_REFERRAL_BONUS: int = 5

    # Referral Program
    REFERRAL_REWARD_AMOUNT: int = 1000  # $10 credit in cents
    REFEREE_REWARD_AMOUNT: int = 500  # $5 discount in cents
    REFERRAL_MINIMUM_DURATION_DAYS: int = 30

    # Google OAuth (ADD THESE)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost/api/v1/auth/google/callback"
    
    # LinkedIn OAuth (ADD THESE)
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "http://localhost/api/v1/auth/linkedin/callback"
    
    # Frontend URL (ADD THIS)
    FRONTEND_URL: str = "http://localhost"

    BROWSER_AUTOMATION_URL: str = "http://browser-automation:3000"
    
        
    def create_upload_dir(self) -> None:
        """Create upload directory if it doesn't exist"""
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path(self.ML_MODEL_PATH).mkdir(parents=True, exist_ok=True)
    
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 

    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Create settings instance
settings = Settings()

# Create necessary directories
settings.create_upload_dir()