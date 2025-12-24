# Testing Guide for Auto-Apply and Hybrid Monitoring

This guide explains how to test the auto-apply and hybrid monitoring features.

## Quick Start

### 1. Automated Tests (Pytest)
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/test_auto_apply_monitoring.py -v

# Run specific test class
pytest tests/test_auto_apply_monitoring.py::TestAutoApply -v
pytest tests/test_auto_apply_monitoring.py::TestHybridMonitoring -v

# Run with coverage
pytest tests/test_auto_apply_monitoring.py --cov=app --cov-report=html
```

### 2. Manual Testing Script
```bash
# Show statistics
python scripts/test_auto_apply.py --stats

# Test browser service
python scripts/test_auto_apply.py --test-browser

# Test auto-apply for a user
python scripts/test_auto_apply.py --user-id YOUR_USER_ID

# Test monitoring for an application
python scripts/test_auto_apply.py --test-monitoring --app-id APPLICATION_ID
```

## Test Coverage

### Auto-Apply Tests
- ✅ CV data extraction
- ✅ Job matching algorithm
- ✅ Custom CV generation
- ✅ Cover letter generation
- ✅ Application record creation
- ✅ Daily limit enforcement
- ✅ Email sending (mocked)
- ✅ Browser automation trigger

### Hybrid Monitoring Tests
- ✅ Browser service health check
- ✅ Domain extraction from URL
- ✅ Email domain scanning
- ✅ Status synthesis logic
- ✅ Application status updates
- ✅ Priority-based decision making

### Integration Tests
- ✅ Full auto-apply workflow
- ✅ End-to-end monitoring flow
- ✅ Database operations
- ✅ External service calls

## Prerequisites

### For Auto-Apply Tests
1. User must have CV uploaded
2. Gmail must be connected (or mocked)
3. Jobs must exist in database
4. Celery worker must be running

### For Monitoring Tests
1. Browser automation service must be running (`npm start` in `browser-automation/`)
2. Application must exist with valid job URL
3. User must have Gmail connected

## Running Tests in CI/CD

Add to `.github/workflows/test.yml`:

```yaml
name: Test Auto-Apply

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:latest
        ports:
          - 27017:27017
      
      redis:
        image: redis:latest
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: pytest tests/test_auto_apply_monitoring.py -v --cov
        env:
          MONGODB_URL: mongodb://localhost:27017
          REDIS_URL: redis://localhost:6379
```

## Troubleshooting

### Tests Fail: "Browser service not reachable"
**Solution**: Start the browser automation service
```bash
cd browser-automation
npm install
npm start
```

### Tests Fail: "No CV data found"
**Solution**: Create test user with CV data (tests should auto-create this)

### Tests Fail: "Gmail API error"
**Solution**: Mock the Gmail service in tests or use test credentials

## Manual End-to-End Test

1. **Setup**
   ```bash
   docker-compose up -d
   cd browser-automation && npm start
   ```

2. **Create Test Data**
   - Register a user
   - Upload a CV
   - Connect Gmail (optional for email tests)
   - Add some jobs to database

3. **Test Auto-Apply**
   ```bash
   python scripts/test_auto_apply.py --user-id YOUR_USER_ID
   ```

4. **Verify Results**
   - Check `applications` collection in MongoDB
   - Verify emails sent (if Gmail connected)
   - Check Celery worker logs

5. **Test Monitoring**
   ```bash
   python scripts/test_auto_apply.py --test-monitoring --app-id APP_ID
   ```

6. **Verify Monitoring**
   - Check application status updated
   - Verify `last_response_check` timestamp
   - Check browser service logs

## Expected Test Results

### Successful Auto-Apply Test
```
🚀 TESTING AUTO-APPLY
✅ Found user: test@example.com
✅ CV Data
✅ Gmail Connected
✅ Auto-Apply Enabled
🎯 Running auto-apply process...
📊 Results:
  Success: True
  Applications Sent: 3
📈 Statistics:
  Jobs Found: 10
  Jobs Analyzed: 10
  Matches Found: 5
  Daily Limit: 5
```

### Successful Monitoring Test
```
🔍 TESTING HYBRID MONITORING
✅ Found application: Software Engineer at Tesla
🔗 Job URL: https://tesla.com/careers/123
✅ Browser service is healthy
🔄 Running hybrid status check...
📊 Results:
  Portal Status: in_review
  Email Status: interview
  Final Status: interview
🎯 Signals Detected (2):
  - browser: in_review
  - email_domain: interview
✅ Application updated
   New status: interview_scheduled
```
