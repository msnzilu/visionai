"""
Configuration settings for the AI Job Application Platform
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Project information
    PROJECT_NAME: str = Field(env="PROJECT_NAME")
    PROJECT_DESCRIPTION: str = "Comprehensive AI-powered job application automation platform"
    PROJECT_VERSION: str = Field(env="PROJECT_VERSION")
    
    # API settings
    API_V1_STR: str = "/api/v1"
    HOST: str = Field(env="HOST")
    PORT: int = Field(env="PORT")
    DEBUG: bool = Field(env="DEBUG")
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(env="REFRESH_TOKEN_EXPIRE_MINUTES")
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = Field(env="PASSWORD_RESET_TOKEN_EXPIRE_HOURS")

    # CORS & Allowed Hosts
    CORS_ORIGINS: List[str] = Field(env="CORS_ORIGINS")
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    MONGODB_URL: str = Field(env="MONGODB_URL")
    DATABASE_NAME: str = Field(env="DATABASE_NAME")
    
    # Redis
    REDIS_URL: str = Field(env="REDIS_URL")
    REDIS_HOST: str = Field(env="REDIS_HOST")
    REDIS_PORT: int = Field(env="REDIS_PORT")
    REDIS_DB: int = Field(env="REDIS_DB")
    CACHE_TTL: int = Field(env="CACHE_TTL")
    
    # OpenAI API
    OPENAI_API_KEY: str = Field(env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(env="OPENAI_TEMPERATURE")
    
    # Stripe
    STRIPE_SECRET_KEY: str = Field(env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str = Field(env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(env="STRIPE_WEBHOOK_SECRET")
    STRIPE_BASIC_PRICE_ID: str = Field(env="STRIPE_BASIC_PRICE_ID")
    STRIPE_PREMIUM_PRICE_ID: str = Field(env="STRIPE_PREMIUM_PRICE_ID")
    
    # Email service
    SMTP_HOST: str = Field(env="SMTP_HOST")
    SMTP_PORT: int = Field(env="SMTP_PORT")
    SMTP_USERNAME: str = Field(env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(env="SMTP_USE_TLS")

    # Mail settings
    MAIL_USERNAME: str = Field(env="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(env="MAIL_PASSWORD")
    MAIL_FROM: str = Field(env="MAIL_FROM")
    MAIL_FROM_NAME: str = Field(env="MAIL_FROM_NAME")
    MAIL_PORT: int = Field(env="MAIL_PORT")
    MAIL_SERVER: str = Field(env="MAIL_SERVER")
    MAIL_STARTTLS: bool = Field(env="MAIL_STARTTLS")
    MAIL_SSL_TLS: bool = Field(env="MAIL_SSL_TLS")
    SUPPORT_EMAIL: str = Field(env="SUPPORT_EMAIL")
    COMPANY_NAME: str = Field(env="COMPANY_NAME")

    # OAuth
    GOOGLE_CLIENT_ID: str = Field(env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(env="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(env="GOOGLE_REDIRECT_URI")
    
    LINKEDIN_CLIENT_ID: str = Field(env="LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET: str = Field(env="LINKEDIN_CLIENT_SECRET")
    LINKEDIN_REDIRECT_URI: str = Field(env="LINKEDIN_REDIRECT_URI")
    
    # Frontend URL
    FRONTEND_URL: str = Field(env="FRONTEND_URL")

    # Job board APIs
    INDEED_PUBLISHER_ID: str = Field(env="INDEED_PUBLISHER_ID")
    INDEED_API_KEY: str = Field(env="INDEED_API_KEY")
    
    # File storage
    UPLOAD_DIR: str = Field(env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(env="MAX_FILE_SIZE")
    MAX_UPLOAD_SIZE: int = Field(env="MAX_UPLOAD_SIZE")
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".doc", ".txt"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(env="RATE_LIMIT_PERIOD")
    
    # Subscription limits - Free Tier
    FREE_TIER_MONTHLY_ATTEMPTS: int = Field(env="FREE_TIER_MONTHLY_ATTEMPTS")
    FREE_TIER_JOBS_PER_ATTEMPT: int = Field(env="FREE_TIER_JOBS_PER_ATTEMPT")
    
    # Subscription limits - Basic Tier
    BASIC_TIER_DAILY_ATTEMPTS: int = Field(env="BASIC_TIER_DAILY_ATTEMPTS")
    BASIC_TIER_MONTHLY_ATTEMPTS: int = Field(env="BASIC_TIER_MONTHLY_ATTEMPTS")
    BASIC_TIER_JOBS_PER_ATTEMPT: int = Field(env="BASIC_TIER_JOBS_PER_ATTEMPT")
    BASIC_TIER_PRICE: int = Field(env="BASIC_TIER_PRICE")
    
    # Subscription limits - Premium Tier
    PREMIUM_TIER_MONTHLY_ATTEMPTS: int = Field(env="PREMIUM_TIER_MONTHLY_ATTEMPTS")
    PREMIUM_TIER_JOBS_PER_ATTEMPT: int = Field(env="PREMIUM_TIER_JOBS_PER_ATTEMPT")
    PREMIUM_TIER_PRICE: int = Field(env="PREMIUM_TIER_PRICE")
    
    # Referral system
    REFERRALS_FOR_FREE_ATTEMPT: int = Field(env="REFERRALS_FOR_FREE_ATTEMPT")
    BASIC_REFERRAL_BONUS: int = Field(env="BASIC_REFERRAL_BONUS")
    PREMIUM_REFERRAL_BONUS: int = Field(env="PREMIUM_REFERRAL_BONUS")
    
    # Browser automation service
    BROWSER_AUTOMATION_URL: str = Field(env="BROWSER_AUTOMATION_URL")
    AUTOMATION_SERVICE_TOKEN: str = Field(default="your-secret-token-here", env="AUTOMATION_SERVICE_TOKEN")

    
    # Machine Learning
    ML_MODEL_PATH: str = Field(env="ML_MODEL_PATH")
    ML_TRAINING_DATA_PATH: str = Field(env="ML_TRAINING_DATA_PATH")
    ML_RETRAIN_INTERVAL_DAYS: int = Field(env="ML_RETRAIN_INTERVAL_DAYS")
    
    # Scraping Configuration
    SCRAPER_USER_AGENT: str = Field(env="SCRAPER_USER_AGENT")
    SCRAPER_DELAY_MIN: int = Field(env="SCRAPER_DELAY_MIN")
    SCRAPER_DELAY_MAX: int = Field(env="SCRAPER_DELAY_MAX")
    
    # Logging
    LOG_LEVEL: str = Field(env="LOG_LEVEL")
    LOG_FILE: str = Field(env="LOG_FILE")
    
    # Background tasks
    CELERY_BROKER_URL: str = Field(env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(env="CELERY_RESULT_BACKEND")
    
    # Webhooks
    WEBHOOK_SECRET: str = Field(env="WEBHOOK_SECRET")
    
    def create_upload_dir(self) -> None:
        """Create upload directory if it doesn't exist"""
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path(self.ML_MODEL_PATH).mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Create settings instance
settings = Settings()

# Create necessary directories
settings.create_upload_dir()
