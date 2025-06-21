#!/bin/bash
# run_tests.sh - Test runner for European Soccer Analytics

set -e

echo "🧪 Running European Soccer Analytics Tests"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run tests in container
run_container_tests() {
    echo -e "${BLUE}Running tests in Docker container...${NC}"
    
    if ! docker-compose ps | grep -q "app.*Up"; then
        echo -e "${YELLOW}Starting containers...${NC}"
        docker-compose up -d
        sleep 20
    fi
    
    echo -e "${BLUE}Running unit tests...${NC}"
    docker-compose exec -T app python -m pytest tests/unit/ -v
    
    echo -e "${BLUE}Running integration tests...${NC}"
    docker-compose exec -T app python -m pytest tests/integration/ -v
    
    echo -e "${BLUE}Testing API connectivity...${NC}"
    docker-compose exec -T app python src/soccer_analytics/etl/test_api.py
    
    echo -e "${BLUE}Testing database connection...${NC}"
    docker-compose exec -T app python -c "
from soccer_analytics.config.database import check_db_connection, init_db
if check_db_connection():
    print('✅ Database connection successful')
    try:
        init_db()
        print('✅ Database initialization successful')
    except Exception as e:
        print(f'⚠️  Database already initialized: {e}')
else:
    print('❌ Database connection failed')
    exit(1)
"
}

# Function to run tests locally
run_local_tests() {
    echo -e "${BLUE}Running tests locally...${NC}"
    
    if command -v poetry &> /dev/null; then
        echo "Using Poetry..."
        poetry run pytest tests/ -v
    elif [ -f "venv/bin/activate" ]; then
        echo "Using virtual environment..."
        source venv/bin/activate
        python -m pytest tests/ -v
    else
        echo "Using system Python..."
        python -m pytest tests/ -v
    fi
}

# Check command line argument
if [ "$1" = "--local" ]; then
    run_local_tests
else
    run_container_tests
fi

echo -e "${GREEN}🎉 All tests completed!${NC}" 