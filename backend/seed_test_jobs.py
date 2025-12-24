"""
Simple seed script for test jobs
Run with: python seed_test_jobs.py
"""

import asyncio
from datetime import datetime, timedelta
import random
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Direct MongoDB connection (bypass app config)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "vision_ai")  # Fixed: underscore

# 10 Test Jobs for Auto-Apply Testing
TEST_JOBS = [
    {
        "title": "Junior Python Developer",
        "company_name": "TechStart Inc",
        "location": "Remote",
        "description": """We're looking for a Junior Python Developer to join our growing team.

Responsibilities:
• Write clean Python code
• Work with REST APIs
• Collaborate with senior developers
• Participate in code reviews

Requirements:
• 1+ years Python experience
• Git version control
• Strong problem-solving skills""",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_level": "junior",
        "salary_range": {"min_amount": 50000, "max_amount": 70000, "currency": "USD", "period": "yearly"},
        "skills_required": ["Python", "Git", "REST APIs"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "TechStart Inc", "contact": {"email": "jobs@techstart.com"}},
        "tags": ["python", "junior", "remote"]
    },
    {
        "title": "Frontend Developer",
        "company_name": "WebCraft Studios",
        "location": "New York, NY",
        "description": """Join our creative team building modern web interfaces.

What you'll do:
• Build responsive UIs with React
• Collaborate with designers
• Optimize for performance

Requirements:
• 2+ years React experience
• Strong CSS/HTML skills
• JavaScript/TypeScript""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "mid_level",
        "salary_range": {"min_amount": 80000, "max_amount": 110000, "currency": "USD", "period": "yearly"},
        "skills_required": ["React", "JavaScript", "CSS", "HTML"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "WebCraft Studios", "contact": {"email": "careers@webcraft.com"}},
        "tags": ["frontend", "react", "hybrid"]
    },
    {
        "title": "Data Analyst",
        "company_name": "DataDriven Co",
        "location": "Chicago, IL",
        "description": """Analyze data to drive business decisions.

Responsibilities:
• Create reports and dashboards
• Analyze trends
• Work with stakeholders

Requirements:
• SQL proficiency
• Excel/Python for analysis
• Strong communication skills""",
        "employment_type": "full_time",
        "work_arrangement": "on_site",
        "experience_level": "mid_level",
        "salary_range": {"min_amount": 65000, "max_amount": 85000, "currency": "USD", "period": "yearly"},
        "skills_required": ["SQL", "Excel", "Python", "Data Analysis"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "DataDriven Co", "contact": {"email": "jobs@datadriven.com"}},
        "tags": ["data", "analytics", "sql"]
    },
    {
        "title": "DevOps Engineer",
        "company_name": "CloudScale Systems",
        "location": "Remote - US",
        "description": """Help us build and scale cloud infrastructure.

Responsibilities:
• Manage CI/CD pipelines
• Monitor production systems
• Automate infrastructure

Requirements:
• AWS/GCP experience
• Docker/Kubernetes
• Linux administration""",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_level": "senior",
        "salary_range": {"min_amount": 120000, "max_amount": 160000, "currency": "USD", "period": "yearly"},
        "skills_required": ["AWS", "Docker", "Kubernetes", "Linux", "CI/CD"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "CloudScale Systems", "contact": {"email": "recruiting@cloudscale.com"}},
        "tags": ["devops", "cloud", "remote"],
        "is_featured": True
    },
    {
        "title": "Full Stack Developer",
        "company_name": "BuildRight Software",
        "location": "Austin, TX",
        "description": """Build end-to-end web applications.

Responsibilities:
• Frontend and backend development
• Database design
• API development

Requirements:
• React/Vue + Node.js
• SQL/NoSQL databases
• RESTful API design""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "mid_level",
        "salary_range": {"min_amount": 90000, "max_amount": 130000, "currency": "USD", "period": "yearly"},
        "skills_required": ["React", "Node.js", "PostgreSQL", "REST APIs"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "BuildRight Software", "contact": {"email": "jobs@buildright.com"}},
        "tags": ["fullstack", "web"]
    },
    {
        "title": "QA Engineer",
        "company_name": "QualityFirst Labs",
        "location": "Seattle, WA",
        "description": """Ensure product quality through testing.

Responsibilities:
• Write automated tests
• Manual testing
• Bug reporting

Requirements:
• Selenium/Cypress experience
• Python or JavaScript
• Attention to detail""",
        "employment_type": "full_time",
        "work_arrangement": "on_site",
        "experience_level": "mid_level",
        "salary_range": {"min_amount": 75000, "max_amount": 100000, "currency": "USD", "period": "yearly"},
        "skills_required": ["Selenium", "Python", "Test Automation", "Cypress"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "QualityFirst Labs", "contact": {"email": "talent@qualityfirst.com"}},
        "tags": ["qa", "testing", "automation"]
    },
    {
        "title": "Machine Learning Engineer",
        "company_name": "AI Innovations",
        "location": "San Francisco, CA",
        "description": """Build ML models to power our AI products.

Responsibilities:
• Train and deploy ML models
• Feature engineering
• Model optimization

Requirements:
• Python, TensorFlow/PyTorch
• ML/Deep Learning experience
• Statistics background""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "senior",
        "salary_range": {"min_amount": 150000, "max_amount": 200000, "currency": "USD", "period": "yearly"},
        "skills_required": ["Python", "TensorFlow", "Machine Learning", "Deep Learning"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "AI Innovations", "contact": {"email": "ml-jobs@aiinnovations.com"}},
        "tags": ["ml", "ai", "python"],
        "is_featured": True
    },
    {
        "title": "Backend Developer - Node.js",
        "company_name": "ServerLogic Inc",
        "location": "Remote",
        "description": """Build scalable backend services.

Responsibilities:
• Design REST/GraphQL APIs
• Database optimization
• Microservices architecture

Requirements:
• Node.js/Express
• MongoDB/PostgreSQL
• AWS/GCP""",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_level": "mid_level",
        "salary_range": {"min_amount": 85000, "max_amount": 120000, "currency": "USD", "period": "yearly"},
        "skills_required": ["Node.js", "Express", "MongoDB", "PostgreSQL", "AWS"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "ServerLogic Inc", "contact": {"email": "jobs@serverlogic.com"}},
        "tags": ["backend", "nodejs", "remote"]
    },
    {
        "title": "UI/UX Designer",
        "company_name": "DesignHub Agency",
        "location": "Los Angeles, CA",
        "description": """Create beautiful user experiences.

Responsibilities:
• User research
• Wireframes and prototypes
• Design systems

Requirements:
• Figma/Sketch proficiency
• UX research experience
• Strong visual design skills""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "mid_level",
        "salary_range": {"min_amount": 70000, "max_amount": 100000, "currency": "USD", "period": "yearly"},
        "skills_required": ["Figma", "UI Design", "UX Research", "Prototyping"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "DesignHub Agency", "contact": {"email": "design@designhub.com"}},
        "tags": ["design", "ux", "ui"]
    },
    {
        "title": "Software Engineer Intern",
        "company_name": "LearnCode Academy",
        "location": "Remote",
        "description": """Summer internship for aspiring developers.

What you'll learn:
• Real-world development
• Agile methodology
• Code review best practices

Requirements:
• CS student or bootcamp grad
• Basic programming knowledge
• Eager to learn""",
        "employment_type": "internship",
        "work_arrangement": "remote",
        "experience_level": "entry_level",
        "salary_range": {"min_amount": 25, "max_amount": 35, "currency": "USD", "period": "hourly"},
        "skills_required": ["Python", "JavaScript", "Git"],
        "external_url": "https://example.com/apply",
        "source": "company_website",
        "company_info": {"name": "LearnCode Academy", "contact": {"email": "internships@learncode.com"}},
        "tags": ["internship", "entry", "learning"]
    }
]


async def seed_jobs():
    """Seed the database with test jobs"""
    
    print(f"🌱 Seeding {len(TEST_JOBS)} test jobs to MongoDB...")
    print(f"   URL: {MONGODB_URL}")
    print(f"   Database: {DATABASE_NAME}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    jobs_collection = db.jobs
    
    # Check connection
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    now = datetime.utcnow()
    inserted_count = 0
    
    for i, job_data in enumerate(TEST_JOBS, 1):
        # Add timestamps and status
        days_ago = random.randint(0, 14)
        posted_date = now - timedelta(days=days_ago)
        
        job = {
            **job_data,
            "posted_date": posted_date,
            "created_at": posted_date,
            "updated_at": posted_date,
            "status": "active",
            "view_count": random.randint(10, 200),
            "application_count": random.randint(0, 20),
            "external_id": f"test_job_{i}",
            "requirements": [],
            "benefits": [],
            "skills_preferred": [],
        }
        
        try:
            await jobs_collection.insert_one(job)
            inserted_count += 1
            print(f"   ✅ {i}/{len(TEST_JOBS)}: {job['title']} at {job['company_name']}")
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
    
    print(f"\n✅ Successfully inserted {inserted_count}/{len(TEST_JOBS)} test jobs!")
    
    # Count total
    total = await jobs_collection.count_documents({"status": "active"})
    print(f"📊 Total active jobs in database: {total}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_jobs())
