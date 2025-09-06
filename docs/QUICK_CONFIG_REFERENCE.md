# Tech Blog CMS - Quick Configuration Reference

## Essential Files

1. **`.env`** - Environment variables (create from `.env.example`)
2. **`docker-compose.yml`** - Service orchestration
3. **`techblog_cms/settings.py`** - Django settings
4. **`nginx/conf.d/default.conf`** - Web server configuration

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# 2. For development
cp docker-compose.override.yml.example docker-compose.override.yml

# 3. Start services
docker-compose up -d

# 4. Initialize database
docker-compose exec django python manage.py migrate

# 5. Create admin user
docker-compose exec django python manage.py createsuperuser
```

## Key Environment Variables

```bash
# Security
SECRET_KEY=<generate-secure-key>      # python -c "import secrets; print(secrets.token_urlsafe(50))"
DEBUG=False                            # Always False in production

# Database
POSTGRES_USER=techblog_prod_user
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=techblog_prod_db

# Redis
REDIS_PASSWORD=<secure-redis-password>

# Domain
DOMAIN=yourdomain.com
ALLOWED_HOSTS=.yourdomain.com,yourdomain.com
```

## Service Endpoints

- **Application**: http://localhost (dev) / https://yourdomain.com (prod)
- **Admin Panel**: /admin/
- **Health Check**: /health/
- **Readiness Check**: /ready/
- **Static Files**: /static/
- **Media Files**: /media/

## Useful Commands

```bash
# Check production readiness
./scripts/production_checklist.sh

# Database backup
docker-compose exec django python manage.py backup_db

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput

# View logs
docker-compose logs -f django
docker-compose logs -f nginx

# Shell access
docker-compose exec django python manage.py shell
docker-compose exec db psql -U $POSTGRES_USER $POSTGRES_DB
```

## Directory Structure

```
techblog_cms/
├── .env                    # Environment variables (git ignored)
├── docker-compose.yml      # Service definitions
├── docker-compose.override.yml  # Development overrides (git ignored)
├── techblog_cms/          # Django application
│   ├── settings.py        # Main settings
│   ├── settings_production.py  # Production overrides
│   └── management/        # Custom commands
├── nginx/                 # Web server config
│   ├── conf.d/           # Site configurations
│   └── ssl/              # SSL certificates
├── logs/                 # Application logs
├── static/               # Static assets
├── media/                # User uploads
└── backups/              # Database backups
```

## Security Checklist

- [ ] Strong SECRET_KEY generated
- [ ] DEBUG=False in production
- [ ] Database passwords changed from defaults
- [ ] Redis password configured
- [ ] SSL certificates installed
- [ ] ALLOWED_HOSTS properly configured
- [ ] Security headers enabled
- [ ] Regular backups scheduled

## Troubleshooting

1. **Can't connect to database**
   - Check DATABASE_URL format
   - Verify PostgreSQL is running: `docker-compose ps db`

2. **Static files not loading**
   - Run: `docker-compose exec django python manage.py collectstatic`
   - Check nginx volumes in docker-compose.yml

3. **SSL issues**
   - Ensure domain DNS points to server
   - Run: `./scripts/init-letsencrypt.sh`
   - Check: `docker-compose logs certbot`

4. **Application errors**
   - Check logs: `docker-compose logs django`
   - Verify migrations: `docker-compose exec django python manage.py showmigrations`