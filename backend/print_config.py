import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings

print(f"DATABASE_NAME: {settings.DATABASE_NAME}")
print(f"MONGODB_URL: {settings.MONGODB_URL}")
print(f"CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
