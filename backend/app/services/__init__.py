# backend/app/services/__init__.py
"""
Services Package
Exposes core services from their respective sub-packages for cleaner imports.
"""

# Automation Services
from .automation.automation_service import AutomationService
from .automation.browser_automation_service import BrowserAutomationService
from .automation.quick_apply_service import QuickApplyService

# Email Services
from .emails.email_service import EmailService, email_service
from .emails.email_agent_service import EmailAgentService, email_agent_service
from .emails.email_intelligence import EmailIntelligenceService, email_intelligence_service
from .emails.email_response_analyzer import EmailResponseAnalyzer, email_response_analyzer
from .emails.gmail_service import GmailService, gmail_service

# Document Services
from .documents.document_service import DocumentService, document_service
from .documents.pdf_service import PDFService, pdf_service
from .documents.cv_customization_service import CVCustomizationService, cv_customization_service
from .documents.cover_letter_service import CoverLetterService, cover_letter_service

# Auth Services
from .auth.auth_service import AuthService
from .auth.oauth_service import OAuthService
from .auth.password_service import PasswordService
from .auth.security_service import SecurityService

# Intelligence Services
from .intelligence.ai_service import AIService, ai_service
from .intelligence.ml_service import MLService, ml_service
from .intelligence.matching_service import MatchingService

# Job Services
from .jobs.job_service import JobService
from .jobs.job_service_simple import JobServiceSimple
from .jobs.application_tracking_service import ApplicationTrackingService

# Core Services
from .core.analytics_service import AnalyticsService
from .core.blog_service import BlogService
from .core.cache_service import CacheService
from .core.notification_service import NotificationService
from .core.referral_service import ReferralService
from .core.subscription_service import SubscriptionService
