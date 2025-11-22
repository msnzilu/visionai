#!/usr/bin/env python3
"""Clear all jobs and seed with fresh sample data"""

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

async def clear_and_seed():
    """Clear existing jobs and add fresh sample data"""
    
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.job_platform
    
    # First, delete all existing jobs
    delete_result = await db.jobs.delete_many({})
    print(f"🗑️  Deleted {delete_result.deleted_count} existing jobs")
    
    # Now insert fresh sample jobs
    sample_jobs = [
        {
            "title": "Senior Software Engineer",
            "description": "We're looking for an experienced software engineer to join our team. You'll work on cutting-edge technologies and solve complex problems.",
            "company_name": "TechCorp Inc",
            "location": "San Francisco, CA",
            "employment_type": None,
            "work_arrangement": None,
            "experience_level": None,
            "salary_range": None,
            "requirements": [],
            "benefits": [],
            "skills_required": ["Python", "JavaScript", "React"],
            "skills_preferred": ["Docker", "Kubernetes"],
            "status": "active",
            "source": "manual",
            "view_count": 0,
            "application_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Frontend Developer",
            "description": "Join our frontend team to build beautiful, responsive web applications. Experience with React and TypeScript required.",
            "company_name": "WebDesign Co",
            "location": "Remote",
            "employment_type": None,
            "work_arrangement": None,
            "experience_level": None,
            "salary_range": None,
            "requirements": [],
            "benefits": [],
            "skills_required": ["React", "TypeScript", "CSS"],
            "skills_preferred": ["Next.js", "Tailwind"],
            "status": "active",
            "source": "manual",
            "view_count": 0,
            "application_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Data Scientist",
            "description": "Analyze large datasets and build machine learning models. PhD or Masters in Computer Science preferred.",
            "company_name": "AI Solutions Ltd",
            "location": "New York, NY",
            "employment_type": None,
            "work_arrangement": None,
            "experience_level": None,
            "salary_range": None,
            "requirements": [],
            "benefits": [],
            "skills_required": ["Python", "Machine Learning", "Statistics"],
            "skills_preferred": ["TensorFlow", "PyTorch"],
            "status": "active",
            "source": "manual",
            "view_count": 0,
            "application_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "DevOps Engineer",
            "description": "Manage cloud infrastructure and CI/CD pipelines. AWS experience required.",
            "company_name": "CloudTech Systems",
            "location": "Austin, TX",
            "employment_type": None,
            "work_arrangement": None,
            "experience_level": None,
            "salary_range": None,
            "requirements": [],
            "benefits": [],
            "skills_required": ["AWS", "Docker", "Kubernetes"],
            "skills_preferred": ["Terraform", "Jenkins"],
            "status": "active",
            "source": "manual",
            "view_count": 0,
            "application_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Full Stack Developer",
            "description": "Build end-to-end web applications using modern technologies. Startup environment with great benefits.",
            "company_name": "StartupXYZ",
            "location": "Remote",
            "employment_type": None,
            "work_arrangement": None,
            "experience_level": None,
            "salary_range": None,
            "requirements": [],
            "benefits": [],
            "skills_required": ["Node.js", "React", "MongoDB"],
            "skills_preferred": ["GraphQL", "Redis"],
            "status": "active",
            "source": "manual",
            "view_count": 0,
            "application_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Insert jobs
    result = await db.jobs.insert_many(sample_jobs)
    print(f"✅ Successfully inserted {len(result.inserted_ids)} sample jobs!")
    
    # Show what was inserted
    for job in sample_jobs:
        print(f"  - {job['title']} at {job['company_name']} ({job['location']})")
    
    client.close()

if __name__ == "__main__":
    print("🔄 Clearing database and seeding with sample jobs...")
    asyncio.run(clear_and_seed())
    print("\n✨ Database ready! Refresh your jobs page to see the results.")
