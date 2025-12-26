# backend/app/services/emails/__init__.py
"""
Email Services Package
Contains services for email sending, composition, intelligence, and Gmail integration
"""

from .email_service import EmailService, email_service
from .email_agent_service import EmailAgentService, email_agent_service
from .email_intelligence import EmailIntelligenceService, email_intelligence_service
from .email_response_analyzer import EmailResponseAnalyzer, email_response_analyzer
from .gmail_service import GmailService, gmail_service

__all__ = [
    'EmailService', 'email_service',
    'EmailAgentService', 'email_agent_service',
    'EmailIntelligenceService', 'email_intelligence_service',
    'EmailResponseAnalyzer', 'email_response_analyzer',
    'GmailService', 'gmail_service'
]
