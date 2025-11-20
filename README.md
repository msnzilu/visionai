# Vision.AI - AI-Powered Job Application Platform

> Automate your job search with intelligent CV customization, job matching, and application tracking

## 📖 Overview

Vision.AI is an AI-powered platform that streamlines the job application process by automatically customizing CVs and cover letters for each job posting, tracking applications, and matching candidates with relevant opportunities. Built with FastAPI, MongoDB, and OpenAI integration.

## ✨ Features

### Core Functionality

- **Smart CV Processing** - Upload and parse CVs using AI to extract structured data
- **Job Search Integration** - Scrape jobs from Indeed, LinkedIn, Glassdoor, and RemoteOK
- **Intelligent Matching** - AI-powered algorithm matches your profile with suitable positions
- **Document Generation** - Auto-generate customized CVs and cover letters for each application
- **Browser Automation** - Automated form filling and job application submission
- **Application Tracking** - Monitor all applications in one centralized dashboard

### Technical Features

- **User Authentication** - Secure JWT-based authentication system
- **Document Management** - Upload, store, and process CVs in multiple formats (PDF, DOCX, TXT)
- **RESTful API** - Comprehensive API with OpenAPI documentation
- **Real-time Notifications** - Track application status and updates
- **Analytics Dashboard** - Visualize application metrics and success rates
- **Subscription Management** - Tiered pricing with Stripe integration

## 🏗️ Architecture

### Backend Stack

- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT tokens with bcrypt password hashing
- **AI/ML**: OpenAI GPT for text processing and generation
- **Task Queue**: Celery with Redis for background jobs
- **Job Scraping**: Playwright for browser automation
- **File Processing**: PyPDF2, python-docx for document parsing

### Frontend Stack

- **Core**: Vanilla JavaScript (ES6+)
- **Styling**: Custom CSS with responsive design
- **Charts**: Chart.js for analytics visualization
- **HTTP Client**: Axios for API communication

### Browser Automation Service

- **Runtime**: Node.js with Express
- **Automation**: Playwright for cross-browser support
- **Form Detection**: ML-based field classification
- **Site Handlers**: Custom handlers for major job boards

## 🎯 Use Cases

1. **Job Seekers** - Automate repetitive application tasks and track all applications
2. **Career Changers** - Generate tailored CVs for different industries
3. **Recruiters** - Bulk process candidate CVs and match with job requirements
4. **Students** - Apply to multiple internships with customized applications

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Built with ❤️ using FastAPI, MongoDB, and OpenAI**
