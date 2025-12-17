import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# DB Config
MONGO_URI = os.getenv("MONGO_URL", "mongodb://mongo:27017") 
DB_NAME = os.getenv("MONGO_DB_NAME", "vision_ai")

async def seed_jobs():
    print(f"Connecting to {MONGO_URI} (DB: {DB_NAME})...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Complete Schema based on models/job.py
    sample_jobs = [
        {
            "title": "Senior Software Engineer",
            "external_id": "seed_job_001",  # Unique identifier for seed data
            "description": "We are looking for a Python/React expert to join our core engineering team. " * 5,
            "company_name": "TechCorp Inc.",
            "location": "Remote",
            "employment_type": "full_time",
            "work_arrangement": "remote",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 140000, 
                "max_amount": 180000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com", # Critical for Auto-Apply
            "application_url": "https://techcorp.example.com/apply",
            "company_info": {
                "name": "TechCorp Inc.",
                "description": "Leading provider of AI solutions.",
                "website": "https://techcorp.example.com",
                "size": "medium",
                "industry": "technology",
                "founded_year": 2015,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://techcorp.example.com"
                },
                "headquarters": {
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "5+ years of Python experience", "is_required": True, "priority": "high"},
                {"requirement": "Experience with React/Next.js", "is_required": True, "priority": "medium"},
                {"requirement": "Docker and Kubernetes knowledge", "is_required": False, "priority": "low"}
            ],
            "benefits": [
                {"name": "Health Insurance", "category": "health"},
                {"name": "Unlimited PTO", "category": "time_off"},
                {"name": "Remote Work Stipend", "category": "financial"}
            ],
            "skills_required": ["Python", "React", "FastAPI", "MongoDB"],
            "skills_preferred": ["AWS", "Docker", "Redis"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "Product Manager",
            "external_id": "seed_job_002",
            "description": "Lead our new product line for enterprise customers. " * 5,
            "company_name": "Innovate Ltd",
            "location": "New York, NY",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 110000, 
                "max_amount": 150000, 
                "currency": "USD", 
                "period": "yearly"
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "company_info": {
                "name": "Innovate Ltd",
                "description": "Innovating the future of finance.",
                "website": "https://innovate.example.com",
                "size": "large",
                "industry": "finance",
                "contact": {
                    "email": "jcharlesmail8@gmail.com"
                }
            },
            "requirements": [
                {"requirement": "3+ years of Product Management", "is_required": True, "priority": "high"},
                {"requirement": "Strong analytical skills", "is_required": True, "priority": "high"}
            ],
            "skills_required": ["Product Management", "JIRA", "Agile", "SQL"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Frontend Developer",
            "external_id": "seed_job_003",
            "description": "Vue.js and Tailwind CSS developer needed for agency work. " * 5,
            "company_name": "Creative Studio",
            "location": "London, UK",
            "employment_type": "contract",
            "work_arrangement": "flexible",
            "experience_level": "junior",
            "salary_range": {
                "min_amount": 400, 
                "max_amount": 600, 
                "currency": "GBP", 
                "period": "daily"
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "company_info": {
                "name": "Creative Studio",
                "size": "small",
                "industry": "media"
            },
            "skills_required": ["Vue.js", "JavaScript", "CSS", "Tailwind"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Data Scientist",
            "external_id": "seed_job_004",
            "description": "Machine learning and big data analysis for healthcare. " * 5,
            "company_name": "DataFlow Analytics",
            "location": "San Francisco, CA",
            "employment_type": "full_time",
            "experience_level": "senior",
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "skills_required": ["Python", "Pandas", "Scikit-learn", "TensorFlow"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Remote Python Developer",
            "external_id": "seed_job_005",
            "description": "Backend API development with FastAPI and PostgreSQL. " * 5,
            "company_name": "CloudSystems",
            "location": "Remote",
            "employment_type": "full_time",
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "skills_required": ["Python", "Django", "PostgreSQL", "AWS"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]

    try:
        # Clear existing seed data to allow re-running script
        print("Clearing existing seed jobs...")
        delete_result = await db.jobs.delete_many({
            "source": "manual",
            "external_id": {"$regex": "^seed_job_"}
        })
        print(f"Deleted {delete_result.deleted_count} existing seed jobs")
        
        print(f"Inserting {len(sample_jobs)} sample jobs with COMPLETE schema...")
        result = await db.jobs.insert_many(sample_jobs)
        print(f"Success! Inserted IDs: {result.inserted_ids}")
        
        # Verify
        count = await db.jobs.count_documents({"status": "active"})
        print(f"Total Active Jobs now: {count}")
    except Exception as e:
        print(f"Error seeding jobs: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_jobs())