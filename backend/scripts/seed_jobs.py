"""
Seed script to add realistic job data to MongoDB for testing
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
from app.core.config import settings

# Realistic job data with real company career URLs
JOBS_DATA = [
    {
        "title": "Senior Full Stack Developer",
        "company_name": "Google",
        "location": "Mountain View, CA",
        "description": """Join Google as a Senior Full Stack Developer to build innovative web applications that serve billions of users.

Key Responsibilities:
• Design and develop scalable full-stack applications
• Collaborate with cross-functional teams (designers, PMs, engineers)
• Write clean, maintainable, and well-tested code
• Mentor junior developers and conduct code reviews
• Drive technical decisions and architecture

Requirements:
• 5+ years of full-stack development experience
• Strong proficiency in JavaScript, React, Node.js, Python
• Experience with cloud platforms (GCP, AWS)
• Bachelor's degree in Computer Science or equivalent
• Excellent problem-solving and communication skills

Nice to Have:
• Experience with microservices architecture
• Knowledge of GraphQL, Docker, Kubernetes
• Open source contributions""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "senior",
        "salary_range": {
            "min_amount": 150000,
            "max_amount": 200000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["JavaScript", "React", "Node.js", "Python", "AWS", "Docker"],
        "skills_preferred": ["TypeScript", "Kubernetes", "GraphQL"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://careers.google.com/jobs/results/",
        "source": "company_website",
        "company_info": {"name": "Google", "contact": {"email": "careers@google.com"}},
        "tags": ["engineering", "web", "senior"],
        "is_featured": True
    },
    {
        "title": "Junior Python Developer",
        "company_name": "Microsoft",
        "location": "Seattle, WA",
        "description": """Microsoft is hiring Junior Python Developers to work on cutting-edge cloud technologies.

What You'll Do:
• Develop and maintain Python applications
• Work with Azure cloud services
• Collaborate with senior engineers
• Learn best practices in software development
• Contribute to team projects and sprints

Requirements:
• 1-2 years of Python development experience
• Understanding of OOP and data structures
• Familiarity with Git and version control
• Strong willingness to learn
• Good communication skills

We Offer:
• Mentorship from senior engineers
• Professional development opportunities
• Work-life balance
• Comprehensive benefits package""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "junior",
        "salary_range": {
            "min_amount": 80000,
            "max_amount": 110000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Python", "Git", "SQL", "REST APIs"],
        "skills_preferred": ["Django", "FastAPI", "Azure", "Docker"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://careers.microsoft.com/us/en",
        "source": "company_website",
        "company_info": {"name": "Microsoft", "contact": {"email": "careers@microsoft.com"}},
        "tags": ["python", "backend", "junior"]
    },
    {
        "title": "Remote Frontend Engineer",
        "company_name": "Shopify",
        "location": "Remote - United States",
        "description": """Shopify is looking for a Remote Frontend Engineer to build beautiful commerce experiences.

Your Role:
• Build responsive web applications using React
• Optimize application performance and accessibility
• Implement pixel-perfect designs from Figma
• Write comprehensive unit and integration tests
• Collaborate asynchronously with global team

Requirements:
• 3+ years of frontend development experience
• Expert knowledge of React, JavaScript, TypeScript
• Strong understanding of HTML, CSS, and web standards
• Experience with modern build tools (Webpack, Vite)
• Proven remote work experience

Perks:
• 100% remote work
• Flexible working hours
• Home office stipend
• Professional development budget""",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_level": "mid_level",
        "salary_range": {
            "min_amount": 120000,
            "max_amount": 160000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["React", "JavaScript", "TypeScript", "CSS", "HTML"],
        "skills_preferred": ["Next.js", "Redux", "Jest", "Webpack"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.shopify.com/careers",
        "source": "company_website",
        "company_info": {"name": "Shopify", "contact": {"email": "talent@shopify.com"}},
        "tags": ["frontend", "react", "remote"],
        "is_featured": True
    },
    {
        "title": "DevOps Engineer",
        "company_name": "Amazon Web Services",
        "location": "Austin, TX",
        "description": """AWS is seeking a DevOps Engineer to help build and scale cloud infrastructure.

Responsibilities:
• Design and implement CI/CD pipelines
• Manage Kubernetes clusters and containerized applications
• Automate infrastructure provisioning with Terraform
• Monitor system performance and implement SRE practices
• Ensure security and compliance standards

Requirements:
• 5+ years of DevOps/SRE experience
• Deep knowledge of AWS services
• Experience with Kubernetes, Docker
• Proficiency in Python or Go
• Strong Linux/Unix skills

Benefits:
• Competitive compensation and stock
• Comprehensive health coverage
• Career growth opportunities
• Work on cutting-edge technology""",
        "employment_type": "full_time",
        "work_arrangement": "on_site",
        "experience_level": "senior",
        "salary_range": {
            "min_amount": 140000,
            "max_amount": 180000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["AWS", "Kubernetes", "Docker", "Terraform", "Python"],
        "skills_preferred": ["Jenkins", "Ansible", "Prometheus", "Grafana"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.amazon.jobs/en/teams/aws",
        "source": "company_website",
        "company_info": {"name": "Amazon Web Services", "contact": {"email": "aws-jobs@amazon.com"}},
        "tags": ["devops", "cloud", "infrastructure"]
    },
    {
        "title": "Machine Learning Engineer",
        "company_name": "Meta",
        "location": "Menlo Park, CA",
        "description": """Join Meta's AI team to build ML systems that impact billions of users worldwide.

What You'll Work On:
• Develop and deploy ML models at massive scale
• Research and implement state-of-the-art ML algorithms
• Optimize model performance and inference speed
• Collaborate with researchers and product teams
• Build ML infrastructure and tooling

Requirements:
• 5+ years of ML engineering experience
• Strong programming skills in Python
• Deep understanding of ML frameworks (PyTorch, TensorFlow)
• Experience with distributed systems
• MS or PhD in CS/ML preferred

Why Meta:
• Work on cutting-edge AI research
• Top-tier compensation and equity
• World-class team and resources
• Impact billions of users""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "senior",
        "salary_range": {
            "min_amount": 180000,
            "max_amount": 250000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning"],
        "skills_preferred": ["Computer Vision", "NLP", "Distributed Systems", "Spark"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.metacareers.com/",
        "source": "company_website",
        "company_info": {"name": "Meta", "contact": {"email": "recruiting@meta.com"}},
        "tags": ["ml", "ai", "python", "senior"],
        "is_featured": True
    },
    {
        "title": "Backend Software Engineer",
        "company_name": "Stripe",
        "location": "San Francisco, CA",
        "description": """Build the financial infrastructure powering internet commerce at Stripe.

Your Impact:
• Design and build scalable API services
• Work on payments processing infrastructure
• Ensure high availability (99.99%+ uptime)
• Write well-tested, maintainable code
• Shape architecture decisions

Requirements:
• 3-5 years of backend development
• Strong in at least one: Ruby, Python, Java, Go
• Experience with SQL and distributed systems
• Understanding of API design principles
• Strong CS fundamentals

What We Offer:
• Competitive salary and equity
• Comprehensive benefits
• Learning and development stipend
• Collaborative culture""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "mid_level",
        "salary_range": {
            "min_amount": 130000,
            "max_amount": 170000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Ruby", "Python", "Java", "SQL", "REST APIs"],
        "skills_preferred": ["Go", "Scala", "Kubernetes", "Redis"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://stripe.com/jobs",
        "source": "company_website",
        "company_info": {"name": "Stripe", "contact": {"email": "jobs@stripe.com"}},
        "tags": ["backend", "api", "payments"]
    },
    {
        "title": "iOS Developer",
        "company_name": "Apple",
        "location": "Cupertino, CA",
        "description": """Create amazing experiences for millions of iPhone and iPad users at Apple.

Role Overview:
• Develop native iOS applications
• Implement beautiful, intuitive user interfaces
• Optimize app performance and battery life
• Work with SwiftUI and UIKit
• Collaborate with design and product teams

Requirements:
• 3+ years of iOS development experience
• Expert knowledge of Swift and iOS SDK
• Published apps in the App Store
• Strong understanding of iOS design patterns
• Passion for great user experience

Why Apple:
• Work on products used by millions
• Competitive compensation
• Employee stock purchase plan
• Product discounts
• Excellent benefits""",
        "employment_type": "full_time",
        "work_arrangement": "on_site",
        "experience_level": "mid_level",
        "salary_range": {
            "min_amount": 140000,
            "max_amount": 180000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Swift", "iOS", "UIKit", "Xcode", "Git"],
        "skills_preferred": ["SwiftUI", "Combine", "CoreData", "ARKit"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.apple.com/careers/us/",
        "source": "company_website",
        "company_info": {"name": "Apple", "contact": {"email": "jobs@apple.com"}},
        "tags": ["ios", "mobile", "swift"]
    },
    {
        "title": "Data Scientist",
        "company_name": "Netflix",
        "location": "Los Gatos, CA",
        "description": """Help Netflix make data-driven decisions that improve the streaming experience.

Responsibilities:
• Analyze complex datasets to extract actionable insights
• Build predictive models and recommendation systems
• Design and analyze A/B tests
• Create data visualizations and dashboards
• Partner with product and engineering teams

Requirements:
• 5+ years of data science experience
• Advanced degree in quantitative field (MS/PhD)
• Expert in Python, SQL, and statistical analysis
• Experience with ML frameworks
• Strong communication skills

Netflix Culture:
• Unlimited vacation policy
• Freedom and responsibility
• Top-tier compensation
• Industry-leading benefits""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "senior",
        "salary_range": {
            "min_amount": 160000,
            "max_amount": 210000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Python", "SQL", "Statistics", "Machine Learning", "Data Analysis"],
        "skills_preferred": ["R", "Spark", "Tableau", "Experiment Design"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://jobs.netflix.com/",
        "source": "company_website",
        "company_info": {"name": "Netflix", "contact": {"email": "talent@netflix.com"}},
        "tags": ["data", "analytics", "ml"],
        "is_featured": True
    },
    {
        "title": "Cloud Solutions Architect",
        "company_name": "IBM",
        "location": "New York, NY",
        "description": """Design and implement enterprise cloud solutions for Fortune 500 clients at IBM.

Key Duties:
• Architect cloud migration strategies
• Lead technical implementations
• Advise clients on cloud best practices
• Create detailed technical documentation
• Mentor junior architects and engineers

Requirements:
• 7+ years in cloud technologies
• Cloud certifications (AWS/Azure/GCP Solutions Architect)
• Experience with enterprise architecture
• Strong client-facing skills
• Knowledge of hybrid cloud strategies

IBM Benefits:
• Competitive compensation
• Comprehensive health coverage
• Professional development programs
• Flexible work arrangements""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "lead",
        "salary_range": {
            "min_amount": 150000,
            "max_amount": 190000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["AWS", "Azure", "Cloud Architecture", "Kubernetes", "Terraform"],
        "skills_preferred": ["GCP", "Microservices", "Security", "Cost Optimization"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.ibm.com/careers",
        "source": "company_website",
        "company_info": {"name": "IBM", "contact": {"email": "careers@ibm.com"}},
        "tags": ["cloud", "architecture", "enterprise"]
    },
    {
        "title": "Frontend Developer",
        "company_name": "GitLab",
        "location": "Remote - Worldwide",
        "description": """Join GitLab's all-remote team and work from anywhere in the world!

What You'll Do:
• Build features for GitLab's web application
• Contribute to the Vue.js codebase
• Collaborate asynchronously with global team
• Improve UI/UX of the platform
• Write comprehensive tests

Requirements:
• 3+ years of frontend development
• Strong Vue.js and JavaScript skills
• Experience working remotely
• Self-motivated and independent
• Excellent written communication

GitLab Perks:
• 100% remote (work from anywhere)
• Flexible working hours
• Home office budget ($3,000)
• Co-working space allowance
• Learning & development budget""",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_level": "mid_level",
        "salary_range": {
            "min_amount": 110000,
            "max_amount": 150000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Vue.js", "JavaScript", "HTML", "CSS", "Git"],
        "skills_preferred": ["Ruby on Rails", "GraphQL", "Jest", "CI/CD"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://about.gitlab.com/jobs/",
        "source": "company_website",
        "company_info": {"name": "GitLab", "contact": {"email": "jobs@gitlab.com"}},
        "tags": ["vue", "frontend", "remote", "async"],
        "is_featured": True
    },
    {
        "title": "Security Engineer",
        "company_name": "Cloudflare",
        "location": "Austin, TX",
        "description": """Protect the internet at scale as a Security Engineer at Cloudflare.

Responsibilities:
• Identify and mitigate security vulnerabilities
• Design security systems and protocols
• Respond to security incidents
• Conduct penetration testing and security audits
• Develop security tools and automation

Requirements:
• 5+ years in security engineering
• Strong knowledge of network security
• Experience with penetration testing
• Programming skills (Python, Go)
• Security certifications preferred (CISSP, CEH, OSCP)

Why Cloudflare:
• Mission-driven company
• Competitive compensation and equity
• Full health benefits
• Professional development budget
• Collaborative culture""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "senior",
        "salary_range": {
            "min_amount": 150000,
            "max_amount": 200000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Security", "Penetration Testing", "Network Security", "Python", "Linux"],
        "skills_preferred": ["Bug Bounty", "Cryptography", "Go", "Reverse Engineering"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.cloudflare.com/careers/",
        "source": "company_website",
        "company_info": {"name": "Cloudflare", "contact": {"email": "recruiting@cloudflare.com"}},
        "tags": ["security", "infosec", "cybersecurity"]
    },
    {
        "title": "Product Manager - AI",
        "company_name": "OpenAI",
        "location": "San Francisco, CA",
        "description": """Drive the development of AI products that will shape the future at OpenAI.

Your Role:
• Define product vision and strategy for AI products
• Work closely with engineers and researchers
• Prioritize features and manage roadmap
• Gather user feedback and iterate
• Communicate product updates to stakeholders

Requirements:
• 5+ years of product management experience
• Technical background (CS degree or equivalent)
• Understanding of AI/ML technologies
• Strong analytical and communication skills
• Experience shipping ML products

OpenAI Offers:
• Competitive salary and equity
• Work on cutting-edge AI technology
• Comprehensive benefits
• Collaborative research environment""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "senior",
        "salary_range": {
            "min_amount": 170000,
            "max_amount": 220000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Product Management", "AI/ML", "Analytics", "Roadmap Planning"],
        "skills_preferred": ["Python", "Data Analysis", "User Research", "Agile"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://openai.com/careers/",
        "source": "company_website",
        "company_info": {"name": "OpenAI", "contact": {"email": "careers@openai.com"}},
        "tags": ["product", "ai", "ml", "pm"],
        "is_featured": True
    },
    {
        "title": "Full Stack Engineer",
        "company_name": "Airbnb",
        "location": "San Francisco, CA",
        "description": """Build the future of travel technology at Airbnb as a Full Stack Engineer.

What You'll Build:
• End-to-end features for Airbnb platform
• Both frontend (React) and backend (Ruby/Java) systems
• Scalable services handling millions of users
• Internal tools for hosts and guests
• Data-driven experiences

Requirements:
• 4+ years of full-stack development
• Strong in React, JavaScript/TypeScript
• Backend experience (Ruby, Java, or Python)
• Database design skills (SQL, NoSQL)
• System design knowledge

Airbnb Benefits:
• Competitive pay and RSUs
• Quarterly travel stipend
• Flexible PTO
• Health and wellness benefits
• Employee stock purchase plan""",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_level": "mid_level",
        "salary_range": {
            "min_amount": 140000,
            "max_amount": 190000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["React", "JavaScript", "Ruby", "SQL", "REST APIs"],
        "skills_preferred": ["TypeScript", "Java", "GraphQL", "Redis"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://careers.airbnb.com/",
        "source": "company_website",
        "company_info": {"name": "Airbnb", "contact": {"email": "talent@airbnb.com"}},
        "tags": ["fullstack", "web", "travel"]
    },
    {
        "title": "Site Reliability Engineer",
        "company_name": "Uber",
        "location": "San Francisco, CA",
        "description": """Ensure the reliability and scalability of Uber's global platform as an SRE.

Responsibilities:
• Monitor and maintain production systems
• Implement automation and tooling
• Incident response and post-mortems
• Capacity planning and optimization
• Collaborate with engineering teams

Requirements:
• 4+ years of SRE/DevOps experience
• Strong Linux/Unix systems knowledge
• Programming skills (Python, Go)
• Experience with monitoring tools (Prometheus, Grafana)
• Understanding of distributed systems

Uber Perks:
• Competitive compensation
• Uber credits monthly
• Comprehensive insurance
• 401k matching
• Commuter benefits""",
        "employment_type": "full_time",
        "work_arrangement": "on_site",
        "experience_level": "mid_level",
        "salary_range": {
            "min_amount": 145000,
            "max_amount": 185000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Linux", "Python", "Kubernetes", "Monitoring", "Automation"],
        "skills_preferred": ["Go", "Terraform", "Ansible", "Incident Management"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.uber.com/us/en/careers/",
        "source": "company_website",
        "company_info": {"name": "Uber", "contact": {"email": "recruiting@uber.com"}},
        "tags": ["sre", "reliability", "devops"]
    },
    {
        "title": "QA Automation Engineer",
        "company_name": "Salesforce",
        "location": "Remote - US",
        "description": """Join Salesforce to build automated testing frameworks for enterprise software.

What You'll Do:
• Design and implement automated test suites
• Develop testing frameworks and tools
• Write and maintain test scripts
• Perform load and performance testing
• Work with developers to ensure quality

Requirements:
• 3+ years of QA automation experience
• Strong programming skills (Java, Python, JavaScript)
• Experience with testing frameworks (Selenium, Cypress)
• Understanding of CI/CD pipelines
• API testing experience

Salesforce Benefits:
• Flexible remote work
• Competitive salary
• Comprehensive benefits
• Professional development
• Volunteer time off""",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_level": "mid_level",
        "salary_range": {
            "min_amount": 110000,
            "max_amount": 145000,
            "currency": "USD",
            "period": "yearly"
        },
        "skills_required": ["Selenium", "Python", "Java", "Test Automation", "CI/CD"],
        "skills_preferred": ["Cypress", "Jest", "API Testing", "Performance Testing"],
        "requirements": [],
        "benefits": [],
        "external_url": "https://www.salesforce.com/company/careers/",
        "source": "company_website",
        "company_info": {"name": "Salesforce", "contact": {"email": "careers@salesforce.com"}},
        "tags": ["qa", "testing", "automation"]
    }
]


async def seed_jobs():
    """Seed the database with realistic job data"""
    
    print(f"🌱 Seeding {len(JOBS_DATA)} realistic jobs...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    jobs_collection = db.jobs
    
    # Clear existing jobs (optional)
    print("🗑️  Clearing existing jobs...")
    await jobs_collection.delete_many({})
    
    now = datetime.utcnow()
    inserted_count = 0
    
    for i, job_data in enumerate(JOBS_DATA, 1):
        # Add timestamps and status
        days_ago = random.randint(0, 30)
        posted_date = now - timedelta(days=days_ago)
        
        job = {
            **job_data,
            "posted_date": posted_date,
            "created_at": posted_date,
            "updated_at": posted_date,
            "status": "active",
            "view_count": random.randint(10, 500),
            "application_count": random.randint(0, 50),
            "external_id": f"{job_data['company_name'].lower().replace(' ', '_')}_{i}",
        }
        
        try:
            await jobs_collection.insert_one(job)
            inserted_count += 1
            print(f"   ✅ {i}/{len(JOBS_DATA)}: {job['title']} at {job['company_name']}")
        except Exception as e:
            print(f"   ❌ Failed to insert job {i}: {str(e)}")
    
    print(f"\n✅ Successfully inserted {inserted_count}/{len(JOBS_DATA)} jobs")
    
    # Print statistics
    print("\n📊 Job Statistics:")
    print(f"   Companies: {len(set(j['company_name'] for j in JOBS_DATA))}")
    print(f"   Locations: {len(set(j['location'] for j in JOBS_DATA))}")
    print(f"   Remote jobs: {sum(1 for j in JOBS_DATA if j['work_arrangement'] == 'remote')}")
    print(f"   Featured jobs: {sum(1 for j in JOBS_DATA if j.get('is_featured', False))}")
    
    # Close connection
    client.close()
    print("\n✨ Done! Visit http://localhost:3000/jobs to see the jobs")


if __name__ == "__main__":
    asyncio.run(seed_jobs())