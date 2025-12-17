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
    
    # Complete Schema based on models/job.py - 20 NEW JOBS
    sample_jobs = [
        {
            "title": "Security Engineer",
            "external_id": "seed_job_011",
            "description": "Protect our infrastructure and applications from security threats. Conduct penetration testing and security audits. " * 5,
            "company_name": "SecureNet",
            "location": "Washington, DC",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 165000, 
                "max_amount": 210000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://securenet.example.com/apply",
            "company_info": {
                "name": "SecureNet",
                "description": "Leading cybersecurity solutions for enterprise clients.",
                "website": "https://securenet.example.com",
                "size": "large",
                "industry": "cybersecurity",
                "founded_year": 2008,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://securenet.example.com"
                },
                "headquarters": {
                    "city": "Washington",
                    "state": "DC",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "CISSP or similar security certification", "is_required": True, "priority": "high"},
                {"requirement": "7+ years security engineering experience", "is_required": True, "priority": "high"},
                {"requirement": "Penetration testing experience", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Security Clearance Support", "category": "professional"},
                {"name": "Top Tier Health Insurance", "category": "health"},
                {"name": "Training Budget", "category": "education"}
            ],
            "skills_required": ["Cybersecurity", "Network Security", "Linux", "Python"],
            "skills_preferred": ["SIEM", "Cloud Security", "Incident Response"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "Mobile Developer (iOS)",
            "external_id": "seed_job_012",
            "description": "Build beautiful native iOS applications for millions of users. Work with latest Swift and SwiftUI technologies. " * 5,
            "company_name": "AppVenture",
            "location": "San Jose, CA",
            "employment_type": "full_time",
            "work_arrangement": "onsite",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 135000, 
                "max_amount": 170000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://appventure.example.com/apply",
            "company_info": {
                "name": "AppVenture",
                "description": "Creating innovative mobile experiences.",
                "website": "https://appventure.example.com",
                "size": "medium",
                "industry": "mobile",
                "founded_year": 2016,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://appventure.example.com"
                },
                "headquarters": {
                    "city": "San Jose",
                    "state": "CA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "4+ years iOS development", "is_required": True, "priority": "high"},
                {"requirement": "Swift and SwiftUI expertise", "is_required": True, "priority": "high"},
                {"requirement": "Published apps on App Store", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Latest Apple Hardware", "category": "tools"},
                {"name": "Stock Options", "category": "financial"},
                {"name": "Gym Membership", "category": "wellness"}
            ],
            "skills_required": ["Swift", "SwiftUI", "iOS SDK", "Xcode"],
            "skills_preferred": ["Combine", "CoreData", "UIKit"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Blockchain Developer",
            "external_id": "seed_job_013",
            "description": "Develop smart contracts and decentralized applications on Ethereum. Work on cutting-edge Web3 projects. " * 5,
            "company_name": "CryptoBuilders",
            "location": "Remote",
            "employment_type": "contract",
            "work_arrangement": "remote",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 100, 
                "max_amount": 150, 
                "currency": "USD", 
                "period": "hourly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://cryptobuilders.example.com/apply",
            "company_info": {
                "name": "CryptoBuilders",
                "description": "Building the future of decentralized finance.",
                "website": "https://cryptobuilders.example.com",
                "size": "small",
                "industry": "blockchain",
                "founded_year": 2020,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://cryptobuilders.example.com"
                },
                "headquarters": {
                    "city": "Remote",
                    "state": "",
                    "country": "Global"
                }
            },
            "requirements": [
                {"requirement": "Solidity programming experience", "is_required": True, "priority": "high"},
                {"requirement": "Smart contract auditing knowledge", "is_required": True, "priority": "high"},
                {"requirement": "Web3.js or Ethers.js experience", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Crypto Payment Options", "category": "financial"},
                {"name": "Fully Remote", "category": "culture"}
            ],
            "skills_required": ["Solidity", "Ethereum", "Web3", "JavaScript"],
            "skills_preferred": ["Hardhat", "Truffle", "IPFS"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "QA Automation Engineer",
            "external_id": "seed_job_014",
            "description": "Design and implement automated testing frameworks for web and mobile applications. Ensure quality across all platforms. " * 5,
            "company_name": "TestPro",
            "location": "Seattle, WA",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 110000, 
                "max_amount": 140000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": False
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://testpro.example.com/apply",
            "company_info": {
                "name": "TestPro",
                "description": "Quality assurance solutions for modern applications.",
                "website": "https://testpro.example.com",
                "size": "medium",
                "industry": "software",
                "founded_year": 2014,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://testpro.example.com"
                },
                "headquarters": {
                    "city": "Seattle",
                    "state": "WA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "3+ years test automation experience", "is_required": True, "priority": "high"},
                {"requirement": "Selenium or Cypress proficiency", "is_required": True, "priority": "high"},
                {"requirement": "CI/CD integration experience", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Flexible Schedule", "category": "time_off"},
                {"name": "Professional Certification", "category": "education"}
            ],
            "skills_required": ["Selenium", "Python", "Java", "CI/CD"],
            "skills_preferred": ["Cypress", "Playwright", "JUnit"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "AI Research Scientist",
            "external_id": "seed_job_015",
            "description": "Conduct cutting-edge research in natural language processing and computer vision. Publish in top-tier conferences. " * 5,
            "company_name": "Neural Labs",
            "location": "Cambridge, MA",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 180000, 
                "max_amount": 250000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://neurallabs.example.com/apply",
            "company_info": {
                "name": "Neural Labs",
                "description": "Advancing AI research for real-world applications.",
                "website": "https://neurallabs.example.com",
                "size": "medium",
                "industry": "research",
                "founded_year": 2019,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://neurallabs.example.com"
                },
                "headquarters": {
                    "city": "Cambridge",
                    "state": "MA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "PhD in Computer Science or related field", "is_required": True, "priority": "high"},
                {"requirement": "Published papers in top AI conferences", "is_required": True, "priority": "high"},
                {"requirement": "Deep learning framework expertise", "is_required": True, "priority": "high"}
            ],
            "benefits": [
                {"name": "Research Budget", "category": "education"},
                {"name": "Conference Travel", "category": "education"},
                {"name": "Publication Bonus", "category": "financial"}
            ],
            "skills_required": ["Python", "PyTorch", "TensorFlow", "Research"],
            "skills_preferred": ["NLP", "Computer Vision", "Transformers"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "Game Developer (Unity)",
            "external_id": "seed_job_016",
            "description": "Create immersive gaming experiences using Unity engine. Work on AAA mobile and PC games. " * 5,
            "company_name": "PixelForge Studios",
            "location": "Los Angeles, CA",
            "employment_type": "full_time",
            "work_arrangement": "onsite",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 115000, 
                "max_amount": 145000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://pixelforge.example.com/apply",
            "company_info": {
                "name": "PixelForge Studios",
                "description": "Crafting memorable gaming experiences.",
                "website": "https://pixelforge.example.com",
                "size": "medium",
                "industry": "gaming",
                "founded_year": 2015,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://pixelforge.example.com"
                },
                "headquarters": {
                    "city": "Los Angeles",
                    "state": "CA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "3+ years Unity development", "is_required": True, "priority": "high"},
                {"requirement": "C# programming expertise", "is_required": True, "priority": "high"},
                {"requirement": "Shipped at least one commercial game", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Game Development Hardware", "category": "tools"},
                {"name": "Unlimited Gaming Library", "category": "perks"},
                {"name": "Crunch-Free Policy", "category": "culture"}
            ],
            "skills_required": ["Unity", "C#", "3D Math", "Game Design"],
            "skills_preferred": ["Unreal Engine", "Shader Programming", "VR"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Cloud Architect",
            "external_id": "seed_job_017",
            "description": "Design and implement scalable cloud infrastructure for enterprise clients. Lead cloud migration projects. " * 5,
            "company_name": "CloudVerse",
            "location": "Remote",
            "employment_type": "full_time",
            "work_arrangement": "remote",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 175000, 
                "max_amount": 220000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://cloudverse.example.com/apply",
            "company_info": {
                "name": "CloudVerse",
                "description": "Enterprise cloud solutions and consulting.",
                "website": "https://cloudverse.example.com",
                "size": "large",
                "industry": "cloud",
                "founded_year": 2013,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://cloudverse.example.com"
                },
                "headquarters": {
                    "city": "Remote",
                    "state": "",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "AWS Solutions Architect Professional certification", "is_required": True, "priority": "high"},
                {"requirement": "8+ years cloud architecture experience", "is_required": True, "priority": "high"},
                {"requirement": "Experience with multi-cloud environments", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Certification Reimbursement", "category": "education"},
                {"name": "Travel Opportunities", "category": "professional"},
                {"name": "Equity Package", "category": "financial"}
            ],
            "skills_required": ["AWS", "Azure", "GCP", "Terraform"],
            "skills_preferred": ["Kubernetes", "Service Mesh", "FinOps"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "Data Engineer",
            "external_id": "seed_job_018",
            "description": "Build and maintain data pipelines and infrastructure. Work with petabyte-scale datasets. " * 5,
            "company_name": "DataStream Inc",
            "location": "New York, NY",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 130000, 
                "max_amount": 165000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://datastream.example.com/apply",
            "company_info": {
                "name": "DataStream Inc",
                "description": "Big data solutions for financial services.",
                "website": "https://datastream.example.com",
                "size": "large",
                "industry": "finance",
                "founded_year": 2011,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://datastream.example.com"
                },
                "headquarters": {
                    "city": "New York",
                    "state": "NY",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "4+ years data engineering experience", "is_required": True, "priority": "high"},
                {"requirement": "Strong SQL and Python skills", "is_required": True, "priority": "high"},
                {"requirement": "Experience with Spark or Hadoop", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Annual Bonus", "category": "financial"},
                {"name": "Commuter Benefits", "category": "financial"},
                {"name": "Health & Wellness", "category": "health"}
            ],
            "skills_required": ["Python", "SQL", "Spark", "Airflow"],
            "skills_preferred": ["Kafka", "Snowflake", "DBT"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Site Reliability Engineer",
            "external_id": "seed_job_019",
            "description": "Ensure high availability and performance of production systems. Build monitoring and alerting infrastructure. " * 5,
            "company_name": "ReliableOps",
            "location": "San Francisco, CA",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 160000, 
                "max_amount": 195000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://reliableops.example.com/apply",
            "company_info": {
                "name": "ReliableOps",
                "description": "Building reliable distributed systems at scale.",
                "website": "https://reliableops.example.com",
                "size": "medium",
                "industry": "technology",
                "founded_year": 2017,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://reliableops.example.com"
                },
                "headquarters": {
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "5+ years SRE or DevOps experience", "is_required": True, "priority": "high"},
                {"requirement": "Strong Linux and networking knowledge", "is_required": True, "priority": "high"},
                {"requirement": "Experience with observability tools", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "On-Call Compensation", "category": "financial"},
                {"name": "Learning Stipend", "category": "education"},
                {"name": "Flexible PTO", "category": "time_off"}
            ],
            "skills_required": ["Linux", "Kubernetes", "Prometheus", "Grafana"],
            "skills_preferred": ["Terraform", "Python", "Go"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "Mobile Developer (Android)",
            "external_id": "seed_job_020",
            "description": "Develop native Android applications using Kotlin and Jetpack Compose. Build features for millions of users. " * 5,
            "company_name": "MobileFusion",
            "location": "Austin, TX",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 125000, 
                "max_amount": 160000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://mobilefusion.example.com/apply",
            "company_info": {
                "name": "MobileFusion",
                "description": "Creating seamless mobile experiences.",
                "website": "https://mobilefusion.example.com",
                "size": "medium",
                "industry": "mobile",
                "founded_year": 2018,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://mobilefusion.example.com"
                },
                "headquarters": {
                    "city": "Austin",
                    "state": "TX",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "3+ years Android development", "is_required": True, "priority": "high"},
                {"requirement": "Kotlin and Jetpack Compose expertise", "is_required": True, "priority": "high"},
                {"requirement": "Published apps on Google Play", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Latest Android Devices", "category": "tools"},
                {"name": "Stock Options", "category": "financial"},
                {"name": "Relocation Assistance", "category": "professional"}
            ],
            "skills_required": ["Kotlin", "Android SDK", "Jetpack Compose", "MVVM"],
            "skills_preferred": ["Coroutines", "Room", "Retrofit"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Business Intelligence Analyst",
            "external_id": "seed_job_021",
            "description": "Transform data into actionable insights. Build dashboards and reports for executive leadership. " * 5,
            "company_name": "Insights Analytics",
            "location": "Chicago, IL",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 95000, 
                "max_amount": 125000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://insightsanalytics.example.com/apply",
            "company_info": {
                "name": "Insights Analytics",
                "description": "Data-driven decision making for enterprises.",
                "website": "https://insightsanalytics.example.com",
                "size": "large",
                "industry": "consulting",
                "founded_year": 2009,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://insightsanalytics.example.com"
                },
                "headquarters": {
                    "city": "Chicago",
                    "state": "IL",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "3+ years BI experience", "is_required": True, "priority": "high"},
                {"requirement": "Advanced SQL skills", "is_required": True, "priority": "high"},
                {"requirement": "Tableau or Power BI expertise", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Professional Development", "category": "education"},
                {"name": "Hybrid Flexibility", "category": "culture"},
                {"name": "401k Match", "category": "financial"}
            ],
            "skills_required": ["SQL", "Tableau", "Excel", "Statistics"],
            "skills_preferred": ["Python", "R", "Power BI"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Solutions Architect",
            "external_id": "seed_job_022",
            "description": "Design technical solutions for enterprise clients. Work with sales and engineering teams. " * 5,
            "company_name": "Enterprise Solutions Co",
            "location": "Boston, MA",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 155000, 
                "max_amount": 195000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://enterprisesol.example.com/apply",
            "company_info": {
                "name": "Enterprise Solutions Co",
                "description": "Technology solutions for Fortune 500 companies.",
                "website": "https://enterprisesol.example.com",
                "size": "enterprise",
                "industry": "consulting",
                "founded_year": 2006,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://enterprisesol.example.com"
                },
                "headquarters": {
                    "city": "Boston",
                    "state": "MA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "7+ years software architecture experience", "is_required": True, "priority": "high"},
                {"requirement": "Strong communication and presentation skills", "is_required": True, "priority": "high"},
                {"requirement": "Experience with enterprise software", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Sales Commission", "category": "financial"},
                {"name": "Travel Benefits", "category": "professional"},
                {"name": "Executive Training", "category": "education"}
            ],
            "skills_required": ["System Design", "AWS", "Microservices", "API Design"],
            "skills_preferred": ["Azure", "Kubernetes", "Event-Driven Architecture"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "Backend Engineer (Go)",
            "external_id": "seed_job_023",
            "description": "Build high-performance backend services using Go. Work on distributed systems and microservices. " * 5,
            "company_name": "SpeedTech",
            "location": "Remote",
            "employment_type": "full_time",
            "work_arrangement": "remote",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 130000, 
                "max_amount": 165000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://speedtech.example.com/apply",
            "company_info": {
                "name": "SpeedTech",
                "description": "High-performance infrastructure for modern apps.",
                "website": "https://speedtech.example.com",
                "size": "small",
                "industry": "technology",
                "founded_year": 2021,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://speedtech.example.com"
                },
                "headquarters": {
                    "city": "Remote",
                    "state": "",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "3+ years Go programming", "is_required": True, "priority": "high"},
                {"requirement": "Experience with gRPC and Protocol Buffers", "is_required": True, "priority": "high"},
                {"requirement": "Understanding of distributed systems", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Fully Remote", "category": "culture"},
                {"name": "Equity Package", "category": "financial"},
                {"name": "Home Office Budget", "category": "financial"}
            ],
            "skills_required": ["Go", "gRPC", "PostgreSQL", "Docker"],
            "skills_preferred": ["Kubernetes", "Redis", "Kafka"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Network Engineer",
            "external_id": "seed_job_024",
            "description": "Design and maintain enterprise network infrastructure. Implement security and performance optimizations. " * 5,
            "company_name": "NetWorks Global",
            "location": "Dallas, TX",
            "employment_type": "full_time",
            "work_arrangement": "onsite",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 125000, 
                "max_amount": 160000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": False
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://networksglobal.example.com/apply",
            "company_info": {
                "name": "NetWorks Global",
                "description": "Enterprise networking solutions and managed services.",
                "website": "https://networksglobal.example.com",
                "size": "large",
                "industry": "networking",
                "founded_year": 2008,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://networksglobal.example.com"
                },
                "headquarters": {
                    "city": "Dallas",
                    "state": "TX",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "CCNP or equivalent certification", "is_required": True, "priority": "high"},
                {"requirement": "6+ years network engineering experience", "is_required": True, "priority": "high"},
                {"requirement": "BGP and OSPF expertise", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Certification Training", "category": "education"},
                {"name": "On-Call Bonus", "category": "financial"},
                {"name": "Health Insurance", "category": "health"}
            ],
            "skills_required": ["Cisco", "Routing", "Switching", "Firewalls"],
            "skills_preferred": ["SD-WAN", "Network Automation", "Python"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "React Native Developer",
            "external_id": "seed_job_025",
            "description": "Build cross-platform mobile applications with React Native. Deliver pixel-perfect UIs. " * 5,
            "company_name": "CrossPlatform Apps",
            "location": "Remote",
            "employment_type": "contract",
            "work_arrangement": "remote",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 70, 
                "max_amount": 100, 
                "currency": "USD", 
                "period": "hourly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://crossplatform.example.com/apply",
            "company_info": {
                "name": "CrossPlatform Apps",
                "description": "Mobile app development for startups and enterprises.",
                "website": "https://crossplatform.example.com",
                "size": "small",
                "industry": "mobile",
                "founded_year": 2019,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://crossplatform.example.com"
                },
                "headquarters": {
                    "city": "Remote",
                    "state": "",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "3+ years React Native experience", "is_required": True, "priority": "high"},
                {"requirement": "Strong JavaScript and TypeScript", "is_required": True, "priority": "high"},
                {"requirement": "Published apps on both platforms", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Flexible Hours", "category": "time_off"},
                {"name": "Contract to Hire Opportunity", "category": "professional"}
            ],
            "skills_required": ["React Native", "JavaScript", "TypeScript", "Redux"],
            "skills_preferred": ["Native Modules", "Expo", "Firebase"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Salesforce Developer",
            "external_id": "seed_job_026",
            "description": "Customize and extend Salesforce platform. Build Lightning Web Components and Apex solutions. " * 5,
            "company_name": "CRM Solutions Inc",
            "location": "Miami, FL",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 105000, 
                "max_amount": 135000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://crmsolutions.example.com/apply",
            "company_info": {
                "name": "CRM Solutions Inc",
                "description": "Salesforce implementation and consulting services.",
                "website": "https://crmsolutions.example.com",
                "size": "medium",
                "industry": "consulting",
                "founded_year": 2014,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://crmsolutions.example.com"
                },
                "headquarters": {
                    "city": "Miami",
                    "state": "FL",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "Salesforce Platform Developer I certification", "is_required": True, "priority": "high"},
                {"requirement": "3+ years Salesforce development", "is_required": True, "priority": "high"},
                {"requirement": "Lightning Web Components experience", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Certification Reimbursement", "category": "education"},
                {"name": "Trailhead Credits", "category": "education"},
                {"name": "Performance Bonus", "category": "financial"}
            ],
            "skills_required": ["Apex", "Lightning Web Components", "SOQL", "Salesforce"],
            "skills_preferred": ["Integration", "CPQ", "Experience Cloud"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Computer Vision Engineer",
            "external_id": "seed_job_027",
            "description": "Develop computer vision systems for autonomous vehicles. Work with cutting-edge AI technologies. " * 5,
            "company_name": "AutoVision AI",
            "location": "Palo Alto, CA",
            "employment_type": "full_time",
            "work_arrangement": "onsite",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 170000, 
                "max_amount": 230000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://autovision.example.com/apply",
            "company_info": {
                "name": "AutoVision AI",
                "description": "Computer vision for autonomous driving systems.",
                "website": "https://autovision.example.com",
                "size": "medium",
                "industry": "automotive",
                "founded_year": 2018,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://autovision.example.com"
                },
                "headquarters": {
                    "city": "Palo Alto",
                    "state": "CA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "PhD or Masters in Computer Vision", "is_required": True, "priority": "high"},
                {"requirement": "5+ years computer vision experience", "is_required": True, "priority": "high"},
                {"requirement": "Deep learning expertise", "is_required": True, "priority": "high"}
            ],
            "benefits": [
                {"name": "Stock Options", "category": "financial"},
                {"name": "Research Budget", "category": "education"},
                {"name": "Commute Shuttle", "category": "perks"}
            ],
            "skills_required": ["Python", "OpenCV", "PyTorch", "Computer Vision"],
            "skills_preferred": ["SLAM", "3D Reconstruction", "LiDAR"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "Hardware Engineer",
            "external_id": "seed_job_028",
            "description": "Design and test electronic hardware systems. Work on IoT devices and embedded systems. " * 5,
            "company_name": "IoT Devices Corp",
            "location": "San Diego, CA",
            "employment_type": "full_time",
            "work_arrangement": "onsite",
            "experience_level": "mid_level",
            "salary_range": {
                "min_amount": 115000, 
                "max_amount": 145000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://iotdevices.example.com/apply",
            "company_info": {
                "name": "IoT Devices Corp",
                "description": "Smart connected devices for home and industry.",
                "website": "https://iotdevices.example.com",
                "size": "medium",
                "industry": "hardware",
                "founded_year": 2016,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://iotdevices.example.com"
                },
                "headquarters": {
                    "city": "San Diego",
                    "state": "CA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "Electrical Engineering degree", "is_required": True, "priority": "high"},
                {"requirement": "4+ years hardware design experience", "is_required": True, "priority": "high"},
                {"requirement": "PCB design and testing", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Lab Equipment Access", "category": "tools"},
                {"name": "Patent Bonuses", "category": "financial"},
                {"name": "Health Insurance", "category": "health"}
            ],
            "skills_required": ["PCB Design", "Embedded Systems", "C/C++", "Testing"],
            "skills_preferred": ["RF Design", "Signal Processing", "FPGA"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
        },
        {
            "title": "Engineering Manager",
            "external_id": "seed_job_029",
            "description": "Lead a team of software engineers building next-generation products. Balance technical and people management. " * 5,
            "company_name": "GrowthTech",
            "location": "Seattle, WA",
            "employment_type": "full_time",
            "work_arrangement": "hybrid",
            "experience_level": "senior",
            "salary_range": {
                "min_amount": 170000, 
                "max_amount": 220000, 
                "currency": "USD", 
                "period": "yearly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://growthtech.example.com/apply",
            "company_info": {
                "name": "GrowthTech",
                "description": "Fast-growing SaaS company building productivity tools.",
                "website": "https://growthtech.example.com",
                "size": "medium",
                "industry": "software",
                "founded_year": 2019,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://growthtech.example.com"
                },
                "headquarters": {
                    "city": "Seattle",
                    "state": "WA",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "5+ years software engineering experience", "is_required": True, "priority": "high"},
                {"requirement": "2+ years management experience", "is_required": True, "priority": "high"},
                {"requirement": "Strong technical background", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Leadership Training", "category": "education"},
                {"name": "Equity Package", "category": "financial"},
                {"name": "Unlimited PTO", "category": "time_off"}
            ],
            "skills_required": ["Leadership", "Software Engineering", "Agile", "Communication"],
            "skills_preferred": ["Product Management", "Cloud Architecture", "Team Building"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": True
        },
        {
            "title": "WordPress Developer",
            "external_id": "seed_job_030",
            "description": "Build custom WordPress themes and plugins for agency clients. Optimize performance and security. " * 5,
            "company_name": "WebCraft Agency",
            "location": "Remote",
            "employment_type": "contract",
            "work_arrangement": "remote",
            "experience_level": "junior",
            "salary_range": {
                "min_amount": 45, 
                "max_amount": 65, 
                "currency": "USD", 
                "period": "hourly",
                "is_negotiable": True
            },
            "status": "active",
            "source": "manual",
            "application_email": "jcharlesmail8@gmail.com",
            "application_url": "https://webcraft.example.com/apply",
            "company_info": {
                "name": "WebCraft Agency",
                "description": "Digital agency specializing in WordPress solutions.",
                "website": "https://webcraft.example.com",
                "size": "small",
                "industry": "web",
                "founded_year": 2017,
                "contact": {
                    "email": "jcharlesmail8@gmail.com",
                    "website": "https://webcraft.example.com"
                },
                "headquarters": {
                    "city": "Remote",
                    "state": "",
                    "country": "USA"
                }
            },
            "requirements": [
                {"requirement": "2+ years WordPress development", "is_required": True, "priority": "high"},
                {"requirement": "PHP and MySQL proficiency", "is_required": True, "priority": "high"},
                {"requirement": "Theme and plugin development", "is_required": True, "priority": "medium"}
            ],
            "benefits": [
                {"name": "Flexible Schedule", "category": "time_off"},
                {"name": "Growth Opportunities", "category": "professional"}
            ],
            "skills_required": ["WordPress", "PHP", "MySQL", "CSS"],
            "skills_preferred": ["WooCommerce", "ACF", "JavaScript"],
            "posted_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_featured": False
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