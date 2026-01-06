#!/bin/bash
# Initial setup script for Price Tracker Pro
# Usage: ./scripts/setup.sh

set -e

echo "🔧 Setting up Price Tracker Pro..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

command -v python3 >/dev/null 2>&1 || { echo "Error: Python 3 is required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Error: Docker is required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Error: Docker Compose is required"; exit 1; }

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs backups uploads ssl

# Generate .env file if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Generating .env file...${NC}"
    cp env.production.example .env
    
    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    else
        # Linux
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    fi
    
    echo -e "${GREEN}✓ .env file created with random secret key${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create Python virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements_saas.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Build Docker images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.saas.yml build

echo -e "${GREEN}✓ Docker images built${NC}"

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f docker-compose.saas.yml up -d db redis

# Wait for database
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 5

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
docker-compose -f docker-compose.saas.yml run --rm web python -c "from app.database import init_db; init_db()"

echo -e "${GREEN}✓ Database initialized${NC}"

# Start all services
echo -e "${YELLOW}Starting all services...${NC}"
docker-compose -f docker-compose.saas.yml up -d

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "🎉 Price Tracker Pro is now running!"
echo ""
echo "📍 URLs:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "📝 Next steps:"
echo "  1. Edit .env with your API keys (Razorpay, SendGrid)"
echo "  2. Register a user at http://localhost:8000/docs"
echo "  3. Start tracking products!"
echo ""
echo "📚 Documentation:"
echo "  - API Documentation: ./API_DOCUMENTATION.md"
echo "  - Deployment Guide: ./DEPLOYMENT_GUIDE.md"
echo "  - Development Progress: ./DEVELOPMENT_PROGRESS.md"
echo ""
echo "🛠️  Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.saas.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.saas.yml down"
echo "  - Restart: docker-compose -f docker-compose.saas.yml restart"
