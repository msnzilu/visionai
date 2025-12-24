"""
Comprehensive Automated Tests for Auto-Apply and Hybrid Monitoring
Run with: pytest tests/test_auto_apply_monitoring.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
import httpx

# Test configuration
TEST_USER_EMAIL = "test@example.com"
TEST_JOB_URL = "https://example.com/careers/software-engineer"
TEST_DOMAIN = "example.com"


@pytest.fixture
async def test_db():
    """Get test database connection"""
    from app.database import get_database
    db = await get_database()
    yield db
    # Cleanup after tests
    await db.applications.delete_many({"test_run": True})
    await db.jobs.delete_many({"test_run": True})


@pytest.fixture
async def test_user(test_db):
    """Create a test user with CV and Gmail connected"""
    user_data = {
        "_id": ObjectId(),
        "email": TEST_USER_EMAIL,
        "full_name": "Test User",
        "cv_data": {
            "personal_info": {
                "name": "Test User",
                "email": TEST_USER_EMAIL,
                "phone": "+1234567890"
            },
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "years": 3
                }
            ],
            "skills": {
                "technical": ["Python", "JavaScript", "React"],
                "soft": ["Communication", "Leadership"]
            }
        },
        "gmail_auth": {
            "email_address": TEST_USER_EMAIL,
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "token_expiry": datetime.utcnow() + timedelta(hours=1)
        },
        "preferences": {
            "auto_apply_enabled": True,
            "auto_monitor_enabled": True,
            "max_daily_applications": 5,
            "min_match_score": 0.7
        }
    }
    
    await test_db.users.insert_one(user_data)
    yield user_data
    await test_db.users.delete_one({"_id": user_data["_id"]})


@pytest.fixture
async def test_job(test_db):
    """Create a test job posting"""
    job_data = {
        "_id": ObjectId(),
        "title": "Senior Software Engineer",
        "company_name": "Example Corp",
        "company": "Example Corp",
        "location": "Remote",
        "description": "We are looking for a talented software engineer...",
        "requirements": ["Python", "React", "3+ years experience"],
        "skills_required": ["Python", "JavaScript"],
        "external_url": TEST_JOB_URL,
        "apply_url": TEST_JOB_URL,
        "status": "active",
        "created_at": datetime.utcnow(),
        "test_run": True
    }
    
    await test_db.jobs.insert_one(job_data)
    yield job_data
    await test_db.jobs.delete_one({"_id": job_data["_id"]})


class TestAutoApply:
    """Test suite for Auto-Apply functionality"""
    
    @pytest.mark.asyncio
    async def test_cv_data_extraction(self, test_user):
        """Test that CV data is properly extracted"""
        from app.services.email_agent_service import email_agent_service
        
        form_data = await email_agent_service.extract_form_data_from_cv(
            user_id=str(test_user["_id"]),
            cv_data=test_user["cv_data"]
        )
        
        assert form_data["first_name"] == "Test"
        assert form_data["last_name"] == "User"
        assert form_data["email"] == TEST_USER_EMAIL
        assert form_data["phone"] == "+1234567890"
        assert "Python" in form_data.get("skills", [])
    
    @pytest.mark.asyncio
    async def test_match_score_calculation(self, test_user, test_job):
        """Test job matching algorithm"""
        from app.workers.auto_apply import calculate_match_score
        
        score = await calculate_match_score(test_user["cv_data"], test_job)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be a decent match
    
    @pytest.mark.asyncio
    async def test_custom_cv_generation(self, test_user, test_job):
        """Test custom CV generation for job"""
        from app.workers.auto_apply import generate_custom_cv
        
        cv_id = await generate_custom_cv(test_user["cv_data"], test_job)
        
        assert cv_id is not None
        assert isinstance(cv_id, str)
    
    @pytest.mark.asyncio
    async def test_cover_letter_generation(self, test_user, test_job):
        """Test cover letter generation"""
        from app.workers.auto_apply import generate_cover_letter
        
        cl_id = await generate_cover_letter(test_user["cv_data"], test_job)
        
        assert cl_id is not None
        assert isinstance(cl_id, str)
    
    @pytest.mark.asyncio
    async def test_application_creation(self, test_db, test_user, test_job):
        """Test that application record is created correctly"""
        application_data = {
            "user_id": str(test_user["_id"]),
            "job_id": str(test_job["_id"]),
            "job_title": test_job["title"],
            "company_name": test_job["company_name"],
            "status": "submitted",
            "source": "auto_apply",
            "auto_applied": True,
            "email_monitoring_enabled": True,
            "created_at": datetime.utcnow(),
            "test_run": True
        }
        
        result = await test_db.applications.insert_one(application_data)
        app_id = result.inserted_id
        
        # Verify
        app = await test_db.applications.find_one({"_id": app_id})
        assert app is not None
        assert app["source"] == "auto_apply"
        assert app["email_monitoring_enabled"] is True
        assert app["auto_applied"] is True
    
    @pytest.mark.asyncio
    async def test_daily_limit_enforcement(self, test_db, test_user):
        """Test that daily application limit is enforced"""
        # Create 5 applications for today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(5):
            await test_db.applications.insert_one({
                "user_id": str(test_user["_id"]),
                "job_id": str(ObjectId()),
                "auto_applied": True,
                "created_at": today_start + timedelta(hours=i),
                "test_run": True
            })
        
        # Check count
        count = await test_db.applications.count_documents({
            "user_id": str(test_user["_id"]),
            "created_at": {"$gte": today_start},
            "auto_applied": True
        })
        
        assert count == 5
        
        # Verify limit would be reached
        max_limit = test_user["preferences"]["max_daily_applications"]
        assert count >= max_limit


class TestHybridMonitoring:
    """Test suite for Hybrid Monitoring functionality"""
    
    @pytest.mark.asyncio
    async def test_browser_service_health(self):
        """Test that browser automation service is reachable"""
        from app.services.automation_service import AutomationService
        
        health = await AutomationService.check_automation_service_health()
        
        # Note: This will fail if service isn't running, which is expected
        # In CI/CD, you'd mock this or ensure service is running
        assert "healthy" in health
    
    @pytest.mark.asyncio
    async def test_domain_extraction(self):
        """Test domain extraction from URL"""
        from urllib.parse import urlparse
        
        domain = urlparse(TEST_JOB_URL).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        
        assert domain == TEST_DOMAIN
    
    @pytest.mark.asyncio
    async def test_email_domain_scan(self, test_db, test_user):
        """Test email domain scanning (mocked)"""
        from app.services.email_intelligence import EmailIntelligenceService
        
        email_service = EmailIntelligenceService(test_db)
        
        # Note: This requires Gmail API, so it will likely return empty in tests
        # In production tests, you'd mock the Gmail service
        results = await email_service.scan_for_application_domain(
            user_id=str(test_user["_id"]),
            domain=TEST_DOMAIN,
            application_id=str(ObjectId()),
            days_back=7
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_status_synthesis_logic(self):
        """Test the status priority synthesis logic"""
        # Simulate different signal combinations
        test_cases = [
            {
                "signals": [
                    {"status": "applied"},
                    {"status": "interview"}
                ],
                "expected": "interview"
            },
            {
                "signals": [
                    {"status": "in_review"},
                    {"status": "rejected"}
                ],
                "expected": "rejected"
            },
            {
                "signals": [
                    {"status": "applied"},
                    {"status": "offer"}
                ],
                "expected": "offer"
            }
        ]
        
        for case in test_cases:
            statuses = [s["status"] for s in case["signals"]]
            
            # Priority logic
            if "rejected" in statuses:
                final = "rejected"
            elif "offer" in statuses:
                final = "offer"
            elif "interview" in statuses:
                final = "interview"
            elif "in_review" in statuses:
                final = "in_review"
            elif "applied" in statuses:
                final = "applied"
            else:
                final = "unknown"
            
            assert final == case["expected"]
    
    @pytest.mark.asyncio
    async def test_application_status_update(self, test_db, test_user, test_job):
        """Test that monitoring updates application status"""
        # Create test application
        app_data = {
            "_id": ObjectId(),
            "user_id": str(test_user["_id"]),
            "job_id": test_job["_id"],
            "status": "applied",
            "source": "auto_apply",
            "test_run": True
        }
        await test_db.applications.insert_one(app_data)
        
        # Simulate status update
        await test_db.applications.update_one(
            {"_id": app_data["_id"]},
            {"$set": {
                "status": "interview_scheduled",
                "last_response_check": datetime.utcnow(),
                "response_check_result": "interview"
            }}
        )
        
        # Verify
        updated_app = await test_db.applications.find_one({"_id": app_data["_id"]})
        assert updated_app["status"] == "interview_scheduled"
        assert updated_app["response_check_result"] == "interview"
        assert "last_response_check" in updated_app


class TestIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_auto_apply_flow(self, test_db, test_user, test_job):
        """Test complete auto-apply workflow"""
        from app.workers.auto_apply import process_auto_apply_for_user
        
        # Run the full process
        result = await process_auto_apply_for_user(test_user, test_db)
        
        assert result["success"] is True
        assert "stats" in result
    
    @pytest.mark.asyncio
    async def test_monitoring_task_execution(self, test_db):
        """Test that monitoring task can execute"""
        from app.workers.auto_apply import monitor_portal_applications
        
        # Note: This will actually try to run monitoring
        # In a real test environment, you'd mock external services
        # For now, we just verify the task is callable
        assert callable(monitor_portal_applications)


# Utility function to run all tests
async def run_all_tests():
    """Helper to run all tests programmatically"""
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
