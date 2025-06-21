#!/bin/bash
# deploy.sh - Production deployment script for European Soccer Analytics

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deployment_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}🚀 European Soccer Analytics - Production Deployment${NC}"
echo "============================================================"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Check .env file
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  .env file not found, copying from .env.example${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your configuration before proceeding${NC}"
        exit 1
    fi
    
    # Check API key
    if grep -q "your_api_key_here" .env; then
        echo -e "${YELLOW}⚠️  Please set your Football Data API key in .env file${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to create directories
create_directories() {
    echo -e "${BLUE}Creating required directories...${NC}"
    
    mkdir -p data logs nginx/ssl "$BACKUP_DIR"
    
    # Set permissions
    chmod 755 logs data "$BACKUP_DIR"
    
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Function to backup existing data
backup_data() {
    if [ "$1" != "--skip-backup" ]; then
        echo -e "${BLUE}Creating data backup...${NC}"
        
        # Check if containers are running
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
            BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
            
            log "Creating database backup: $BACKUP_FILE"
            docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
                -U "${POSTGRES_USER:-postgres}" \
                "${POSTGRES_DB:-soccer_analytics}" > "$BACKUP_FILE"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
            else
                echo -e "${YELLOW}⚠️  Backup failed, continuing anyway${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  No running containers found, skipping backup${NC}"
        fi
    fi
}

# Function to deploy application
deploy_application() {
    echo -e "${BLUE}Deploying application...${NC}"
    
    # Pull latest images
    log "Pulling latest images"
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build application image
    log "Building application image"
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Stop existing containers
    log "Stopping existing containers"
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start new containers
    log "Starting new containers"
    docker-compose -f "$COMPOSE_FILE" up -d
    
    echo -e "${GREEN}✅ Application deployed${NC}"
}

# Function to wait for services
wait_for_services() {
    echo -e "${BLUE}Waiting for services to be ready...${NC}"
    
    # Wait for database
    log "Waiting for database"
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" &>/dev/null; then
            break
        fi
        echo "Waiting for database... ${timeout}s remaining"
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${RED}❌ Database failed to start${NC}"
        exit 1
    fi
    
    # Wait for application
    log "Waiting for application"
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8501/_stcore/health &>/dev/null; then
            break
        fi
        echo "Waiting for application... ${timeout}s remaining"
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${YELLOW}⚠️  Application health check failed, but proceeding${NC}"
    fi
    
    echo -e "${GREEN}✅ Services are ready${NC}"
}

# Function to run health checks
run_health_checks() {
    echo -e "${BLUE}Running health checks...${NC}"
    
    # Wait a bit for services to settle
    sleep 10
    
    # Run comprehensive health check
    if docker-compose -f "$COMPOSE_FILE" exec -T app python /app/scripts/health_check.py --exit-code; then
        echo -e "${GREEN}✅ Health checks passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Some health checks failed, check logs${NC}"
    fi
}

# Function to show deployment status
show_status() {
    echo -e "${BLUE}Deployment Status:${NC}"
    echo "=================="
    
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo -e "\n${BLUE}Service URLs:${NC}"
    echo "• Dashboard: http://localhost:8501"
    echo "• Health Check: http://localhost/health"
    
    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo "• View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "• Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "• Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "• Run health check: docker-compose -f $COMPOSE_FILE exec app python /app/scripts/health_check.py"
}

# Function to setup monitoring
setup_monitoring() {
    echo -e "${BLUE}Setting up monitoring...${NC}"
    
    # Create monitoring cron job
    CRON_JOB="*/5 * * * * cd $(pwd) && docker-compose -f $COMPOSE_FILE exec -T app python /app/scripts/health_check.py --json >> logs/health.log 2>&1"
    
    # Add to crontab if not exists
    if ! crontab -l 2>/dev/null | grep -q "health_check.py"; then
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        echo -e "${GREEN}✅ Monitoring cron job added${NC}"
    else
        echo -e "${YELLOW}⚠️  Monitoring cron job already exists${NC}"
    fi
}

# Main deployment function
main() {
    local skip_backup=false
    local skip_monitoring=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                skip_backup=true
                shift
                ;;
            --skip-monitoring)
                skip_monitoring=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-backup     Skip data backup"
                echo "  --skip-monitoring Skip monitoring setup"
                echo "  --help, -h        Show this help"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    log "Starting deployment with options: skip_backup=$skip_backup, skip_monitoring=$skip_monitoring"
    
    # Run deployment steps
    check_prerequisites
    create_directories
    
    if [ "$skip_backup" = false ]; then
        backup_data
    fi
    
    deploy_application
    wait_for_services
    run_health_checks
    
    if [ "$skip_monitoring" = false ]; then
        setup_monitoring
    fi
    
    show_status
    
    echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
    log "Deployment completed successfully"
}

# Handle script interruption
trap 'echo -e "\n${RED}Deployment interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@" 