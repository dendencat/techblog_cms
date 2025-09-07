# Tech Blog CMS Configuration Guide

This guide covers all configuration aspects of the Tech Blog CMS application.

## Table of Contents
- [Environment Variables](#environment-variables)
- [Django Settings](#django-settings)
- [Docker Configuration](#docker-configuration)
- [Nginx Configuration](#nginx-configuration)
- [Database Configuration](#database-configuration)
- [Redis Configuration](#redis-configuration)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)

## Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (generate a secure one) | `your-50-char-secret-key` |
| `DEBUG` | Debug mode (False for production) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `.localhost,127.0.0.1,yourdomain.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host:5432/dbname` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/1` |

### Database Credentials

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `techblog` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `techblogpass` |
| `POSTGRES_DB` | PostgreSQL database name | `techblogdb` |

### Optional OAuth Settings

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |

### Security Settings

| Variable | Description | Production Value |
|----------|-------------|------------------|
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `https://yourdomain.com` |
| `SECURE_SSL_REDIRECT` | Force HTTPS redirect | `True` |
| `SESSION_COOKIE_SECURE` | Secure session cookies | `True` |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookies | `True` |

## Django Settings

The main Django settings file is located at `techblog_cms/settings.py`.

### Key Configuration Areas

1. **Secret Key Management**
   ```python
   SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')
   ```

2. **Debug Mode**
   ```python
   DEBUG = config('DEBUG', default=False, cast=bool)
   ```

3. **Database Configuration**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('POSTGRES_DB', 'techblogdb'),
           'USER': os.environ.get('POSTGRES_USER', 'techblog'),
           'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'techblogpass'),
           'HOST': 'db',
           'PORT': '5432',
       }
   }
   ```

4. **Static Files**
   ```python
   STATIC_URL = 'static/'
   STATIC_ROOT = os.path.join(BASE_DIR, 'static')
   ```

## Docker Configuration

### Docker Compose Services

The application uses Docker Compose with the following services:

1. **nginx** - Load balancer and web server
2. **django** - Web application server
3. **db** - PostgreSQL database
4. **redis** - Caching and session storage
5. **static** - Static file server
6. **certbot** - SSL certificate management

### Development Override

For local development, create a `docker-compose.override.yml`:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

This file enables:
- Hot reloading
- Debug mode
- Exposed database ports
- Simplified networking

## Nginx Configuration

### Production Configuration
- HTTPS with TLS 1.2/1.3
- HTTP/2 support
- Security headers (HSTS, X-Frame-Options, etc.)
- OCSP stapling
- Gzip compression

### Development Configuration
- HTTP only on port 80
- Simplified proxy settings
- No SSL requirements

### Key Locations
- Static files: `/static/`
- Media files: `/media/`
- ACME challenges: `/.well-known/acme-challenge/`

## Database Configuration

### PostgreSQL Settings
- Version: 16 (Alpine)
- Default port: 5432
- Data persistence: Docker volume `db_data`

### Connection Pooling
Configure in Django settings:
```python
DATABASES['default']['CONN_MAX_AGE'] = 60
```

### Backup Strategy
Regular backups recommended using:
```bash
docker-compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql
```

## Redis Configuration

### Usage
- Session storage
- Cache backend
- Celery broker (if implemented)

### Security
- Password protection enabled
- Network isolation via Docker networks
- Version: Redis 7 (Alpine)

### Configuration in Django
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
    }
}
```

## SSL/TLS Configuration

### Let's Encrypt Integration
1. Domain configuration in `.env`:
   ```
   DOMAIN=yourdomain.com
   ```

2. Initialize certificates:
   ```bash
   ./scripts/init-letsencrypt.sh
   ```

3. Automatic renewal via Certbot container

### SSL Settings
- Protocols: TLS 1.2, TLS 1.3
- Strong cipher suites
- OCSP stapling enabled
- HSTS with preload

## Development Setup

1. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Create override file**
   ```bash
   cp docker-compose.override.yml.example docker-compose.override.yml
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec django python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec django python manage.py createsuperuser
   ```

## Production Deployment

### Pre-deployment Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set secure database passwords
- [ ] Configure Redis password
- [ ] Enable all security settings
- [ ] Set up SSL certificates
- [ ] Configure backups
- [ ] Set up monitoring

### Deployment Steps

1. **Prepare environment**
   ```bash
   # Copy and configure .env
   cp .env.example .env
   # Edit with production values
   ```

2. **Build and start services**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. **Initialize SSL**
   ```bash
   ./scripts/init-letsencrypt.sh
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec django python manage.py migrate
   ```

5. **Collect static files**
   ```bash
   docker-compose exec django python manage.py collectstatic --noinput
   ```

### Health Checks

Monitor service health:
```bash
docker-compose ps
docker-compose logs -f [service_name]
```

### Scaling

To scale Django workers:
```bash
docker-compose up -d --scale django=3
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check `DATABASE_URL` format
   - Verify PostgreSQL container is running
   - Check network connectivity

2. **Static files not loading**
   - Run `collectstatic` command
   - Check nginx volume mounts
   - Verify `STATIC_ROOT` setting

3. **SSL certificate issues**
   - Ensure domain DNS is configured
   - Check Certbot logs
   - Verify nginx SSL configuration

### Debug Commands

```bash
# Check Django logs
docker-compose logs django

# Access Django shell
docker-compose exec django python manage.py shell

# Check nginx configuration
docker-compose exec nginx nginx -t

# Database console
docker-compose exec db psql -U $POSTGRES_USER $POSTGRES_DB
```