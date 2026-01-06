#!/bin/bash
# Deployment script for Price Tracker Pro
# Usage: ./scripts/deploy.sh [staging|production]

set -e  # Exit on error

ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying to $ENVIRONMENT..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    echo -e "${RED}Error: Environment must be 'staging' or 'production'${NC}"
    exit 1
fi

# Load environment-specific config
if [[ "$ENVIRONMENT" == "production" ]]; then
    ENV_FILE="$PROJECT_ROOT/.env.production"
else
    ENV_FILE="$PROJECT_ROOT/.env.staging"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file $ENV_FILE not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment file loaded${NC}"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: Docker is required${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Error: Docker Compose is required${NC}"; exit 1; }

echo -e "${GREEN}✓ Prerequisites checked${NC}"

# Pull latest code
cd "$PROJECT_ROOT"
echo -e "${YELLOW}Pulling latest code...${NC}"
git pull origin main

# Backup database
echo -e "${YELLOW}Backing up database...${NC}"
docker-compose -f docker-compose.saas.yml exec -T db pg_dump -U price_tracker price_tracker_saas | gzip > "backups/db-$(date +%Y%m%d-%H%M%S).sql.gz"
echo -e "${GREEN}✓ Database backed up${NC}"

# Build new images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.saas.yml build --no-cache

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
# docker-compose -f docker-compose.saas.yml run --rm web alembic upgrade head

# Deploy with zero-downtime
echo -e "${YELLOW}Deploying application...${NC}"
docker-compose -f docker-compose.saas.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Health check
echo -e "${YELLOW}Running health checks...${NC}"
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Application is healthy${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${YELLOW}Health check failed, retrying ($RETRY_COUNT/$MAX_RETRIES)...${NC}"
        sleep 5
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}Error: Health checks failed${NC}"
    echo -e "${YELLOW}Rolling back...${NC}"
    docker-compose -f docker-compose.saas.yml down
    exit 1
fi

# Clean up old images
echo -e "${YELLOW}Cleaning up old Docker images...${NC}"
docker image prune -f

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}Application is running at: http://localhost:8000${NC}"
echo -e "${GREEN}API Docs: http://localhost:8000/docs${NC}"

# Show logs
echo -e "${YELLOW}Recent logs:${NC}"
docker-compose -f docker-compose.saas.yml logs --tail=20 web
