# backend/app/api/__init__.py
"""
API routes package for the AI Job Application Platform
"""

from fastapi import APIRouter

# Import only the modules that actually exist
try:
    from . import auth
    auth_available = True
except ImportError:
    auth_available = False

try:
    from . import documents
    documents_available = True
except ImportError:
    documents_available = False

# Main API router
api_router = APIRouter()

# Include only available route modules
if auth_available:
    api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

if documents_available:
    api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

try:
    from . import migration
    api_router.include_router(migration.router, tags=["migration"])
except ImportError:
    pass


__all__ = ["api_router"]

# Future modules to implement:
# - users
# - jobs  
# - applications
# - subscriptions
# - referrals