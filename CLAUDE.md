# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a Django-based Tech Blog CMS with a Docker containerized architecture:

- **Django Application**: Located in `/techblog_cms/` - contains settings, URLs, views, and WSGI configuration
- **Docker Multi-Service Setup**: 
  - `django`: Django app with Gunicorn (port 8000)
  - `nginx`: Load balancer and reverse proxy (ports 80/443)
  - `db`: PostgreSQL 16 database (port 5432)
  - `redis`: Redis cache (port 6379)
  - `static`: Static file server (port 8080)
  - `certbot`: SSL certificate management

## Common Development Commands

### Running the Application
```bash
# Start all services
docker-compose up -d

# Start only core services (dev)
docker-compose up django db redis

# Stop all services
docker-compose down

# Rebuild and start (after code changes)
docker-compose up --build
```

### Database Operations
```bash
# Run Django commands in container
docker-compose exec django python manage.py <command>

# Create superuser
docker-compose exec django python manage.py createsuperuser

# Run migrations
docker-compose exec django python manage.py migrate

# Create migrations
docker-compose exec django python manage.py makemigrations
```

### Testing
```bash
# Run all tests
python -m pytest -v

# Test configuration is in pytest.ini with Django settings
# Tests should be located in techblog_cms/tests/
```

### Deployment
```bash
# Full deployment script
./deploy.sh

# SSL certificate setup (production)
sudo ./scripts/init-letsencrypt.sh
```

## Project Structure Notes

- **Settings**: Uses python-decouple for environment configuration
- **Database**: PostgreSQL with environment variables for credentials
- **Static Files**: Served via separate Nginx container in production
- **Templates**: Located in `techblog_cms/templates/`
- **WSGI**: Configured in `techblog_cms/wsgi.py` for Gunicorn

## Environment Configuration

The project uses `.env` file for configuration. Copy `.env.example` and modify:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Development mode toggle
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `POSTGRES_*`: Database credentials
- `DOMAIN`: For SSL certificates

## Development Notes

- The project is containerized-first - Django commands should be run inside containers
- No manage.py exists at root level - Django project structure is inside containers
- SSL/HTTPS is configured for production with automatic Let's Encrypt renewal
- CI/CD is set up via GitHub Actions for automated testing and deployment