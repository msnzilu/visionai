import sys
import os

# Add project to Python path
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'app'))

# Set environment variables
os.environ.setdefault('DEPLOYMENT_ENV', 'production')
os.environ.setdefault('DISABLE_CELERY', 'true')
os.environ.setdefault('DISABLE_AUTOMATION', 'true')

# Import FastAPI app
from app.main import app as application

# This is what Passenger looks for
# Don't rename 'application'