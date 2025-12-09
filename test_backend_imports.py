import sys
import os

# Add backend to path
sys.path.append(os.path.abspath("backend"))

try:
    print("Importing app.models.job...")
    from app.models.job import SavedJob, SavedJobResponse
    print("Success importing app.models.job")

    print("Importing app.api.jobs...")
    from app.api.jobs import router
    print("Success importing app.api.jobs")
    
    print("Importing app.services.pdf_service...")
    from app.services.pdf_service import pdf_service
    print("Success importing app.services.pdf_service")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
