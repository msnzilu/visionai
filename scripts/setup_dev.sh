#!/bin/bash
# scripts/setup_dev.sh
# Development Environment Setup for AI Job Application Platform

set -e

echo "🚀 Setting up AI Job Application Platform Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on macOS or Linux
OS="$(uname -s)"
echo "📱 Detected OS: $OS"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3.9+ is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_warning "Node.js not found. Browser automation service will need Node.js 16+"
else
    NODE_VERSION=$(node --version)
    print_status "Node.js $NODE_VERSION found"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. You can still run individual services manually"
else
    print_status "Docker found"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose not found. You can still run individual services manually"
else
    print_status "Docker Compose found"
fi

# Create project directory structure
echo "📁 Creating directory structure..."

mkdir -p backend/app/{api,core,models,schemas,services,integrations,ml,workers}
mkdir -p backend/tests
mkdir -p frontend/{pages,assets/{css,js,images,fonts},components}
mkdir -p browser-automation/src/{automation,ml,utils}
mkdir -p ml-models/{data/{training,validation,test},models,notebooks,scripts}
mkdir -p docs/{api,setup}
mkdir -p scripts
mkdir -p logs
mkdir -p uploads
mkdir -p nginx/{sites-enabled,ssl}

print_status "Directory structure created"

# Setup Backend
echo "🐍 Setting up Backend..."

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    print_status "Backend dependencies installed"
else
    print_warning "requirements.txt not found. Please ensure it exists."
fi

# Install development dependencies
if [ -f "requirements-dev.txt" ]; then
    print_info "Installing development dependencies..."
    pip install -r requirements-dev.txt
    print_status "Development dependencies installed"
fi

# Setup environment file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_info "Creating .env file from .env.example..."
        cp .env.example .env
        print_status ".env file created"
        print_warning "Please update .env file with your actual configuration values"
    else
        print_warning ".env.example not found. Please create .env file manually"
    fi
fi

cd ..

# Setup Frontend
echo "🌐 Setting up Frontend..."

cd frontend

# Check if package.json exists for any frontend build tools
if [ -f "package.json" ]; then
    if command -v npm &> /dev/null; then
        print_info "Installing frontend dependencies..."
        npm install
        print_status "Frontend dependencies installed"
    else
        print_warning "npm not found. Skipping frontend dependency installation"
    fi
fi

cd ..

# Setup Browser Automation
echo "🤖 Setting up Browser Automation..."

cd browser-automation

# Setup Node.js environment
if [ -f "package.json" ] && command -v npm &> /dev/null; then
    print_info "Installing browser automation dependencies..."
    npm install
    print_status "Browser automation dependencies installed"
    
    # Setup environment file
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Browser automation .env file created"
    fi
else
    print_warning "Skipping browser automation setup (Node.js/npm required)"
fi

cd ..

# Setup MongoDB (if using Docker)
echo "🗄️  Database Setup..."

if command -v docker &> /dev/null; then
    print_info "Setting up MongoDB with Docker..."
    
    # Create init script for MongoDB
    cat > scripts/init-mongo.js << 'EOF'
// MongoDB initialization script
db = db.getSiblingDB('job_platform_dev');

// Create initial collections
db.createCollection('users');
db.createCollection('jobs');
db.createCollection('applications');
db.createCollection('subscriptions');
db.createCollection('documents');
db.createCollection('referrals');
db.createCollection('usage_tracking');
db.createCollection('ml_training_data');

print('Database initialized successfully');
EOF

    print_status "MongoDB initialization script created"
else
    print_warning "Docker not available. Please install MongoDB manually"
fi

# Create useful scripts
echo "📝 Creating utility scripts..."

# Create run script
cat > scripts/run_dev.sh << 'EOF'
#!/bin/bash
# Run development environment

echo "🚀 Starting AI Job Application Platform..."

# Start with Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "Starting services with Docker Compose..."
    docker-compose up -d
    echo "✅ Services started!"
    echo "📱 Access points:"
    echo "   - Backend API: http://localhost:8000"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Browser Automation: http://localhost:3001"
    echo "   - API Docs: http://localhost:8000/docs"
    echo "   - Flower (Celery): http://localhost:5555"
else
    echo "Docker Compose not available. Please start services manually."
fi
EOF

chmod +x scripts/run_dev.sh

# Create stop script
cat > scripts/stop_dev.sh << 'EOF'
#!/bin/bash
# Stop development environment

echo "🛑 Stopping AI Job Application Platform..."

if command -v docker-compose &> /dev/null; then
    docker-compose down
    echo "✅ Services stopped!"
else
    echo "Docker Compose not available."
fi
EOF

chmod +x scripts/stop_dev.sh

# Create test script
cat > scripts/run_tests.sh << 'EOF'
#!/bin/bash
# Run tests

echo "🧪 Running tests..."

cd backend
source venv/bin/activate
pytest -v
cd ..

echo "✅ Tests completed!"
EOF

chmod +x scripts/run_tests.sh

print_status "Utility scripts created"

# Create VS Code workspace settings
echo "⚙️  Creating VS Code settings..."

mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./backend/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/node_modules": true,
        "**/.env": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "backend/tests"
    ]
}
EOF

cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Backend",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/backend/venv/bin/uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000"
            ],
            "cwd": "${workspaceFolder}/backend",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/backend"
            },
            "console": "integratedTerminal"
        }
    ]
}
EOF

print_status "VS Code configuration created"

# Final instructions
echo ""
echo "🎉 Development environment setup complete!"
echo ""
print_info "Next steps:"
echo "1. Update backend/.env with your API keys and configuration"
echo "2. Update browser-automation/.env if using browser automation"
echo "3. Start the development environment:"
echo "   ./scripts/run_dev.sh"
echo ""
print_info "Manual startup (without Docker):"
echo "1. Start MongoDB: mongod"
echo "2. Start Redis: redis-server"
echo "3. Start Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "4. Start Frontend: cd frontend && python -m http.server 3000"
echo "5. Start Browser Automation: cd browser-automation && npm start"
echo ""
print_info "Access points:"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🤖 Browser Automation: http://localhost:3001"
echo "🌸 Flower (Celery Monitor): http://localhost:5555"
echo ""
print_warning "Remember to:"
echo "- Configure your API keys in .env files"
echo "- Set up your external service accounts (OpenAI, Stripe, etc.)"
echo "- Review and customize the configuration for your needs"
echo ""
echo "Happy coding! 🚀"