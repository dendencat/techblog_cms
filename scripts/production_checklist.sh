#!/bin/bash

# Production Deployment Checklist Script
# This script helps verify that the system is ready for production deployment

echo "========================================="
echo "Tech Blog CMS Production Checklist"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
READY=true

# Function to check a condition
check() {
    local description=$1
    local command=$2
    
    echo -n "Checking: $description... "
    
    if eval $command > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
    else
        echo -e "${RED}✗ FAIL${NC}"
        READY=false
    fi
}

# Function to check environment variable
check_env() {
    local var_name=$1
    local description=$2
    
    echo -n "Checking: $description... "
    
    if [ -n "${!var_name}" ]; then
        echo -e "${GREEN}✓ SET${NC}"
    else
        echo -e "${RED}✗ NOT SET${NC}"
        READY=false
    fi
}

echo "1. Environment Variables"
echo "------------------------"
check_env "SECRET_KEY" "Django SECRET_KEY"
check_env "POSTGRES_PASSWORD" "PostgreSQL password"
check_env "REDIS_PASSWORD" "Redis password"
check_env "DOMAIN" "Domain name"

echo ""
echo "2. Configuration Files"
echo "----------------------"
check "Environment file exists" "[ -f .env ]"
check "Production settings exist" "[ -f techblog_cms/settings_production.py ]"
check ".env is in .gitignore" "grep -q '^\.env$' .gitignore"

echo ""
echo "3. Security Settings"
echo "-------------------"
check "DEBUG is False" "grep -q 'DEBUG=False' .env"
check "SECRET_KEY is not default" "! grep -q 'django-insecure' .env"
check "SECURE_SSL_REDIRECT is True" "grep -q 'SECURE_SSL_REDIRECT=True' .env"

echo ""
echo "4. Docker Services"
echo "-----------------"
check "Docker is installed" "command -v docker"
check "Docker Compose is installed" "command -v docker-compose"
check "Docker daemon is running" "docker info"

echo ""
echo "5. SSL/TLS Setup"
echo "----------------"
check "SSL init script exists" "[ -f scripts/init-letsencrypt.sh ]"
check "SSL init script is executable" "[ -x scripts/init-letsencrypt.sh ]"
check "Nginx SSL directory exists" "[ -d nginx/ssl ]"

echo ""
echo "6. Directory Structure"
echo "---------------------"
check "Logs directory exists" "[ -d logs ]"
check "Static directory exists" "[ -d static ]"
check "Media directory exists" "[ -d media ] || mkdir -p media"
check "Backups directory exists" "[ -d backups ] || mkdir -p backups"

echo ""
echo "========================================="
if [ "$READY" = true ]; then
    echo -e "${GREEN}✓ System is ready for production deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: docker-compose build"
    echo "2. Run: ./scripts/init-letsencrypt.sh (for SSL setup)"
    echo "3. Run: docker-compose up -d"
    echo "4. Run: docker-compose exec django python manage.py migrate"
    echo "5. Run: docker-compose exec django python manage.py collectstatic --noinput"
    echo "6. Run: docker-compose exec django python manage.py createsuperuser"
else
    echo -e "${RED}✗ System is NOT ready for production deployment${NC}"
    echo ""
    echo "Please fix the issues above before deploying to production."
fi
echo "========================================="

exit $([ "$READY" = true ] && echo 0 || echo 1)