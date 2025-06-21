#!/bin/bash
# setup_and_test.sh - Complete setup and testing for European Soccer Analytics

set -e

echo "🏈 European Soccer Analytics Platform Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file and add your Football Data API key!${NC}"
    echo "Get your free API key from: https://www.football-data.org/client/register"
fi

# Check Docker
echo -e "${BLUE}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed${NC}"

# Clean up any existing containers
echo -e "${BLUE}Cleaning up existing containers...${NC}"
docker-compose down --volumes --remove-orphans 2>/dev/null || true

# Build and start services
echo -e "${BLUE}Building and starting services...${NC}"
docker-compose up --build --detach

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 30

# Check if containers are running
echo -e "${BLUE}Checking container status...${NC}"
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Containers are not running properly${NC}"
    echo "Container status:"
    docker-compose ps
    echo "Logs:"
    docker-compose logs
    exit 1
fi

echo -e "${GREEN}✅ Containers are running${NC}"

# Test database connection
echo -e "${BLUE}Testing database connection...${NC}"
if docker-compose exec -T postgres pg_isready -U postgres; then
    echo -e "${GREEN}✅ Database is ready${NC}"
else
    echo -e "${RED}❌ Database is not ready${NC}"
    docker-compose logs postgres
    exit 1
fi

# Test API
echo -e "${BLUE}Testing Football Data API...${NC}"
if docker-compose exec -T app python src/soccer_analytics/etl/test_api.py; then
    echo -e "${GREEN}✅ API test passed${NC}"
else
    echo -e "${YELLOW}⚠️  API test failed - check your API key${NC}"
fi

# Show dashboard URL
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo "Dashboard URL: http://localhost:8501"
echo ""
echo "Available commands:"
echo "  docker-compose logs          - View all logs"
echo "  docker-compose logs app      - View app logs"
echo "  docker-compose logs postgres - View database logs"
echo "  docker-compose down          - Stop all services"
echo ""
echo "To fetch data:"
echo "  docker-compose exec app python scripts/run_etl.py --competitions PREMIER_LEAGUE"
echo ""
echo -e "${YELLOW}⚠️  Remember to set your real API key in .env file!${NC}" 