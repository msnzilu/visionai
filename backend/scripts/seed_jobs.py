"""
Seed script to add mock job data to MongoDB for testing
Run with: python -m scripts.seed_jobs
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from bson import ObjectId

# Mock job data
COMPANIES = [
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Tesla",
    "Spotify", "Airbnb", "Uber", "Stripe", "Shopify", "Adobe", "Salesforce"
]

JOB_TITLES = [
    "Senior Software Engineer",
    "Full Stack Developer",
    "Frontend Engineer",
    "Backend Engineer",
    "DevOps Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
    "Product Manager",
    "UX Designer",
    "QA Engineer",
    "Cloud Architect",
    "Security Engineer"
]

LOCATIONS = [
    "San Francisco, CA",
    "New York, NY",
    "Seattle, WA",
    "Austin, TX",
    "Boston, MA",
    "Remote",
    "London, UK",
    "Berlin, Germany",
    "Toronto, Canada"
]

INDUSTRIES = [
    "technology", "finance", "healthcare", "education", "retail",
    "media", "consulting", "manufacturing"
]

EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "internship"]
EXPERIENCE_LEVELS = ["entry", "mid", "senior", "lead", "executive"]

SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "AWS",
    "Docker", "Kubernetes", "MongoDB", "PostgreSQL", "Redis", "GraphQL",
    "REST API", "CI/CD", "Git", "Agile", "Scrum", "TDD"
]

BENEFITS = [
    "Health insurance",
    "401(k) matching",
    "Remote work",
    "Flexible hours",
    "Unlimited PTO",
    "Stock options",
    "Learning budget",
    "Gym membership"
]


def generate_job_description(title: str, company: str) -> str:
    """Generate a realistic job description"""
    return f"""We are looking for a talented {title} to join our team at {company}.

Responsibilities:
• Design and develop scalable software solutions
• Collaborate with cross-functional teams
• Write clean, maintainable code
• Participate in code reviews
• Mentor junior developers

Requirements:
• 3+ years of experience in software development
• Strong problem-solving skills
• Experience with modern web technologies
• Excellent communication skills
• Bachelor's degree in Computer Science or related field

Nice to have:
• Experience with cloud platforms (AWS, GCP, Azure)
• Knowledge of microservices architecture
• Open source contributions
"""


async def seed_jobs(num_jobs: int = 50):
    """Seed the database with mock job data"""
    
    print(f"🌱 Seeding {num_jobs} mock jobs...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    jobs_collection = db.jobs
    
    # Clear existing jobs (optional - comment out if you want to keep existing data)
    await jobs_collection.delete_many({})
    print("🗑️  Cleared existing jobs")
    
    jobs = []
    now = datetime.utcnow()
    
    for i in range(num_jobs):
        company = random.choice(COMPANIES)
        title = random.choice(JOB_TITLES)
        location = random.choice(LOCATIONS)
        
        # Random date within last 30 days
        days_ago = random.randint(0, 30)
        posted_date = now - timedelta(days=days_ago)
        
        # Application deadline 30-60 days from posting
        deadline_days = random.randint(30, 60)
        deadline = posted_date + timedelta(days=deadline_days)
        
        # Generate unique application URL with timestamp to avoid duplicates
        unique_id = f"{int(posted_date.timestamp())}_{random.randint(1000, 9999)}"
        
        job = {
            "title": title,
            "company_name": company,  # Changed from company to company_name to match model
            "location": location,
            "description": generate_job_description(title, company),
            "employment_type": random.choice(EMPLOYMENT_TYPES),
            "experience_level": random.choice(EXPERIENCE_LEVELS),
            "salary_min": random.randint(80, 150) * 1000,
            "salary_max": random.randint(150, 250) * 1000,
            "currency": "USD",
            "industry": random.choice(INDUSTRIES),
            "required_skills": random.sample(SKILLS, k=random.randint(3, 6)),
            "preferred_skills": random.sample(SKILLS, k=random.randint(2, 4)),
            "benefits": random.sample(BENEFITS, k=random.randint(3, 5)),
            "remote_allowed": random.choice([True, False]),
            "visa_sponsorship": random.choice([True, False]),
            "application_url": f"https://{company.lower().replace(' ', '')}.com/careers/{unique_id}",
            "source": random.choice(["linkedin", "indeed", "glassdoor", "company_website"]),
            "posted_date": posted_date,
            "application_deadline": deadline,
            "status": "active",
            "is_active": True,
            "view_count": random.randint(0, 500),
            "application_count": random.randint(0, 50),
            "created_at": posted_date,
            "updated_at": posted_date,
            "external_id": unique_id,
            "metadata": {
                "scraped": False,
                "verified": True,
                "featured": random.choice([True, False]),
                "unique_id": unique_id  # Add unique identifier
            }
        }
        
        jobs.append(job)
    
    # Insert jobs one by one to avoid bulk write errors
    inserted_count = 0
    for i, job in enumerate(jobs, 1):
        try:
            await jobs_collection.insert_one(job)
            inserted_count += 1
            if i % 10 == 0:
                print(f"   Inserted {i}/{num_jobs} jobs...")
        except Exception as e:
            print(f"   ⚠️  Failed to insert job {i}: {str(e)}")
    
    print(f"✅ Successfully inserted {inserted_count}/{num_jobs} jobs")
    
    # Print some stats
    print("\n📊 Job Statistics:")
    print(f"   Companies: {len(set(j['company_name'] for j in jobs))}")
    print(f"   Locations: {len(set(j['location'] for j in jobs))}")
    print(f"   Remote jobs: {sum(1 for j in jobs if j['remote_allowed'])}")
    print(f"   Visa sponsorship: {sum(1 for j in jobs if j['visa_sponsorship'])}")
    
    # Close connection
    client.close()
    print("\n✨ Done!")


async def seed_user_applications(user_email: str, num_applications: int = 10):
    """Seed applications for a specific user"""
    
    print(f"\n🌱 Seeding {num_applications} applications for {user_email}...")
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    users_collection = db.users
    jobs_collection = db.jobs
    applications_collection = db.applications
    
    # Get user
    user = await users_collection.find_one({"email": user_email})
    if not user:
        print(f"❌ User {user_email} not found")
        return
    
    # Get random jobs
    jobs = await jobs_collection.aggregate([
        {"$sample": {"size": num_applications}}
    ]).to_list(length=num_applications)
    
    if not jobs:
        print("❌ No jobs found. Run seed_jobs first!")
        return
    
    statuses = ["draft", "submitted", "under_review", "interview_scheduled", 
                "rejected", "accepted", "withdrawn"]
    
    applications = []
    now = datetime.utcnow()
    
    for i, job in enumerate(jobs):
        days_ago = random.randint(0, 60)
        applied_date = now - timedelta(days=days_ago)
        
        application = {
            "user_id": str(user["_id"]),
            "job_id": str(job["_id"]),
            "status": random.choice(statuses),
            "source": "manual",
            "company_name": job["company"],
            "job_title": job["title"],
            "job_location": job["location"],
            "applied_date": applied_date,
            "notes": f"Applied via {job.get('source', 'website')}",
            "resume_version": "default",
            "cover_letter_used": random.choice([True, False]),
            "timeline": [
                {
                    "timestamp": applied_date,
                    "type": "application_submitted",
                    "description": "Application submitted",
                    "metadata": {}
                }
            ],
            "documents": [],
            "communications": [],
            "interviews": [],
            "tasks": [],
            "created_at": applied_date,
            "updated_at": applied_date,
            "deleted_at": None
        }
        
        applications.append(application)
    
    # Insert applications one by one
    inserted_count = 0
    for i, application in enumerate(applications, 1):
        try:
            await applications_collection.insert_one(application)
            inserted_count += 1
        except Exception as e:
            print(f"   ⚠️  Failed to insert application {i}: {str(e)}")
    
    print(f"✅ Successfully created {inserted_count}/{num_applications} applications")
    
    # Print stats
    status_counts = {}
    for app in applications:
        status = app["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\n📊 Application Status Distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")
    
    client.close()
    print("\n✨ Done!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed mock job data")
    parser.add_argument("--jobs", type=int, default=50, help="Number of jobs to create")
    parser.add_argument("--user", type=str, help="User email to create applications for")
    parser.add_argument("--applications", type=int, default=10, help="Number of applications to create")
    
    args = parser.parse_args()
    
    # Seed jobs
    asyncio.run(seed_jobs(args.jobs))
    
    # Seed applications if user specified
    if args.user:
        asyncio.run(seed_user_applications(args.user, args.applications))
