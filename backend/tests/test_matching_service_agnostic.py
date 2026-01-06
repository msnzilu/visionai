import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.intelligence.matching_service import MatchingService

async def test_industry_agnostic_matching():
    service = MatchingService()
    
    print("--- Test 1: Nursing CV (Non-Tech) ---")
    nursing_cv = {
        "experience": [
            {"title": "Senior Registered Nurse", "company": "General Hospital"},
            {"title": "Nurse Practitioner", "company": "City Clinic"}
        ],
        "recommended_roles": [
            "Clinical Care Manager",
            "Health Science Instructor",
            "Patient Advocate"
        ],
        "skills": {
            "technical": ["Patient Care", "BLS", "Electronic Health Records"],
            "soft": ["Empathy", "Communication"]
        }
    }
    
    roles = await service.get_suggested_roles(nursing_cv)
    print(f"Suggested Roles for Nursing CV:")
    for r in roles:
        print(f" - {r['title']} ({r['match_type']})")
    
    titles = [r["title"].lower() for r in roles]
    assert "senior registered nurse" in titles
    assert "nurse practitioner" in titles
    assert "clinical care manager" in titles
    assert "software engineer" not in titles
    print("Test 1 Passed!\n")

    print("--- Test 2: Marketing CV ---")
    marketing_cv = {
        "experience": [
            {"title": "Digital Marketing Manager", "company": "Growth Co"}
        ],
        "recommended_roles": [
            "SEO Specialist",
            "Content Strategist"
        ],
        "skills": ["SEO", "SEM", "Copywriting"]
    }
    
    roles = await service.get_suggested_roles(marketing_cv)
    print(f"Suggested Roles for Marketing CV:")
    for r in roles:
        print(f" - {r['title']} ({r['match_type']})")
    
    titles = [r["title"].lower() for r in roles]
    assert "digital marketing manager" in titles
    assert "seo specialist" in titles
    assert "data scientist" not in titles
    print("Test 2 Passed!\n")

    print("--- Test 3: CV with no AI recommendations ---")
    minimal_cv = {
        "experience": [{"title": "Sales Associate", "company": "Retail Store"}],
        "skills": ["Sales", "Customer Service"]
    }
    roles = await service.get_suggested_roles(minimal_cv)
    print(f"Suggested Roles for Minimal CV:")
    for r in roles:
        print(f" - {r['title']} ({r['match_type']})")
    assert len(roles) == 1
    assert roles[0]["title"] == "Sales Associate"
    print("Test 3 Passed!\n")

if __name__ == "__main__":
    asyncio.run(test_industry_agnostic_matching())
