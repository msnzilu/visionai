# backend/app/services/documents/__init__.py
"""
Document Services Package
Contains services for document management, PDF generation, CV customization, and cover letters.
"""

from .document_service import DocumentService
from .pdf_service import PDFService, pdf_service
from .cv_customization_service import CVCustomizationService, cv_customization_service
from .cover_letter_service import CoverLetterService, cover_letter_service

__all__ = [
    'DocumentService',
    'PDFService', 'pdf_service',
    'CVCustomizationService', 'cv_customization_service',
    'CoverLetterService', 'cover_letter_service'
]
