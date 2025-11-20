# CVision - AI Job Application Platform (Phase 1)

> AI-powered job application automation platform

## 🎯 Phase 1 Goals

✅ **Complete Working Backend** with FastAPI, MongoDB, and authentication  
✅ **CV Upload & Processing** with OpenAI integration  
✅ **Basic Frontend** for testing and user interaction  
✅ **User Authentication** with JWT tokens  
✅ **Document Management** with file upload and processing  

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+ 
- MongoDB (local install or Docker)
- OpenAI API key
- Git

### 2. Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd cvision-platform

# Run setup script
chmod +x scripts/setup_phase1.sh
./scripts/setup_phase1.sh

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY
```

### 3. Start Services
```bash
# Terminal 1: Backend
./scripts/start_backend.sh

# Terminal 2: Frontend  
./scripts/start_frontend.sh

# Or manually:
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
cd frontend && python3 -m http.server 3000
```

### 4. Test the Application
- **Frontend**: http://localhost:3000/pages/index.html
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📁 Required Files for Phase 1

### ✅ Backend Files (All Created)

#### Core Application
- `backend/app/__init__.py` 
- `backend/app/main.py` - FastAPI application entry point
- `backend/app/config.py` - Configuration settings
- `backend/app/database.py` - MongoDB connection
- `backend/app/dependencies.py` - FastAPI dependencies

#### Models & Schemas  
- `backend/app/models/__init__.py`
- `backend/app/models/user.py` - User Pydantic models
- `backend/app/models/common.py` - Common response models

#### Security & Auth
- `backend/app/core/__init__.py`
- `backend/app/core/security.py` - JWT and password hashing

#### API Routes
- `backend/app/api/__init__.py`
- `backend/app/api/auth.py` - Authentication endpoints  
- `backend/app/api/documents.py` - CV upload endpoints

#### Business Logic
- `backend/app/services/__init__.py`
- `backend/app/services/auth_service.py` - Authentication logic
- `backend/app/services/document_service.py` - CV processing
- `backend/app/services/openai_service.py` - OpenAI integration

#### Configuration
- `backend/requirements.txt` - Python dependencies
- `backend/.env.example` - Environment variables template
- `backend/.env` - Your environment variables (create from .example)

### ✅ Frontend Files (All Created)

#### Pages
- `frontend/pages/index.html` - Landing page
- `frontend/pages/login.html` - Login/register page  
- `frontend/pages/dashboard.html` - User dashboard

#### Styles & Scripts
- `frontend/assets/css/main.css` - Main styles
- `frontend/assets/css/auth.css` - Authentication styles
- `frontend/assets/js/main.js` - Main JavaScript
- `frontend/assets/js/auth.js` - Authentication logic

### ✅ Scripts & Tools
- `scripts/setup_phase1.sh` - Automated setup script
- `scripts/start_backend.sh` - Backend startup script  
- `scripts/start_frontend.sh` - Frontend startup script

## 🧪 Testing Phase 1

### 1. Backend API Tests
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@cvision.com",
    "password": "testpass123", 
    "full_name": "Test User"
  }'

# Login  
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@cvision.com",
    "password": "testpass123"
  }'

# Upload CV (replace TOKEN with actual token from login)
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@path/to/your/cv.pdf"
```

### 2. Frontend User Flow
1. **Landing Page**: http://localhost:3000/pages/index.html
2. **Register**: Create new account
3. **Login**: Access dashboard
4. **Upload CV**: Test file upload (PDF/DOCX/TXT)
5. **View Results**: Check parsed CV data

### 3. Expected Results
- ✅ User registration and login works
- ✅ JWT authentication protects endpoints
- ✅ CV files upload successfully  
- ✅ OpenAI processes and extracts CV data
- ✅ Structured data saves to MongoDB
- ✅ Frontend displays CV information

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
SECRET_KEY=your-super-secret-jwt-key
MONGODB_URL=mongodb://localhost:27017

# Optional  
DEBUG=true
DATABASE_NAME=cvision
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### OpenAI Setup
1. Get API key: https://platform.openai.com/api-keys
2. Add to `backend/.env`: `OPENAI_API_KEY=sk-...`
3. Ensure you have credits in your OpenAI account

### MongoDB Setup

#### Option 1: Local Installation
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y mongodb
sudo systemctl start mongodb

# macOS
brew install mongodb-community
brew services start mongodb-community
```

#### Option 2: Docker
```bash
docker run -d --name cvision-mongodb -p 27017:27017 mongo:latest
```

## 🐛 Troubleshooting

### Backend Won't Start
- Check Python virtual environment is activated
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check MongoDB is running: `docker ps | grep mongo`

### OpenAI Errors
- Verify API key in `.env` file
- Check OpenAI account has credits
- Test API key: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`

### File Upload Fails
- Check `backend/uploads/` directory exists and is writable
- Verify file size under 10MB limit
- Ensure file type is PDF, DOCX, or TXT

### CORS Issues
- Frontend must run on port 3000 or update `BACKEND_CORS_ORIGINS` in config
- Check browser network tab for specific errors

## 📊 Phase 1 Success Metrics

- [ ] ✅ Backend starts without errors
- [ ] ✅ API documentation accessible at `/docs`
- [ ] ✅ User registration/login works
- [ ] ✅ CV upload processes successfully  
- [ ] ✅ OpenAI extracts structured data
- [ ] ✅ Frontend displays parsed CV information
- [ ] ✅ Data persists in MongoDB
- [ ] ✅ All endpoints return expected responses

## 🔄 Next Steps (Phase 2)

Once Phase 1 is working:
1. **Job Search Integration** - Add job board APIs
2. **Job Matching Algorithm** - Match CVs to jobs
3. **Document Generation** - Create custom CVs and cover letters  
4. **Enhanced Frontend** - Job listings and application tracking

## 📚 Development Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **MongoDB Docs**: https://docs.mongodb.com/
- **OpenAI API**: https://platform.openai.com/docs/
- **JWT Tokens**: https://jwt.io/

## 🆘 Support

If you encounter issues:
1. Check the logs: `docker-compose logs` or backend terminal output
2. Verify all environment variables are set
3. Test individual components (MongoDB, OpenAI API)
4. Check the `/health` endpoint for system status

---

**Total Setup Time**: 15-30 minutes  
**Files Created**: ~20 core files  
**Features Working**: Authentication, CV upload, OpenAI processing, data storage  
**Ready For**: Phase 2 development (job search and matching)