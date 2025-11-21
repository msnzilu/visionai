# Mock Job Data Seeding Guide

This guide shows you how to populate your database with mock job data for testing.

## Quick Start

### 1. Seed 50 Mock Jobs
```bash
cd backend
python -m scripts.seed_jobs
```

### 2. Seed Custom Number of Jobs
```bash
python -m scripts.seed_jobs --jobs 100
```

### 3. Seed Jobs + Applications for Your User
```bash
python -m scripts.seed_jobs --jobs 50 --user jcharlesmail1@gmail.com --applications 15
```

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--jobs` | Number of jobs to create | 50 |
| `--user` | User email to create applications for | None |
| `--applications` | Number of applications to create | 10 |

## Examples

**Create 100 jobs:**
```bash
python -m scripts.seed_jobs --jobs 100
```

**Create jobs and 20 applications for your account:**
```bash
python -m scripts.seed_jobs --user jcharlesmail1@gmail.com --applications 20
```

**Just create applications (if jobs already exist):**
```bash
python -m scripts.seed_jobs --jobs 0 --user jcharlesmail1@gmail.com --applications 10
```

## What Gets Created

### Jobs Include:
- ✅ Realistic job titles (Senior Software Engineer, Data Scientist, etc.)
- ✅ Real company names (Google, Microsoft, Amazon, etc.)
- ✅ Various locations (San Francisco, Remote, etc.)
- ✅ Salary ranges ($80k-$250k)
- ✅ Required and preferred skills
- ✅ Benefits packages
- ✅ Application deadlines
- ✅ Remote work options
- ✅ Visa sponsorship info

### Applications Include:
- ✅ Various statuses (submitted, under_review, interview_scheduled, etc.)
- ✅ Timeline events
- ✅ Application dates
- ✅ Notes and metadata

## Running from Docker

If your backend is running in Docker:

```bash
docker exec -it vision_ai_backend python -m scripts.seed_jobs --jobs 50 --user jcharlesmail1@gmail.com --applications 15
```

## Verify the Data

After seeding, you can verify in MongoDB:

```bash
# Connect to MongoDB
docker exec -it vision_ai_mongo mongosh vision_ai

# Check jobs count
db.jobs.countDocuments()

# View a sample job
db.jobs.findOne()

# Check applications
db.applications.countDocuments()

# View applications for your user
db.applications.find({"user_id": "YOUR_USER_ID"})
```

## Clear Data (Optional)

To clear all jobs before seeding:

Uncomment line 117 in `seed_jobs.py`:
```python
await jobs_collection.delete_many({})
```

Then run the seed script again.
