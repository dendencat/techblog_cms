import os
import sys
from pathlib import Path
from decouple import config, Csv
from urllib.parse import urlparse, unquote

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS configuration
# ALLOWED_HOSTS configuration
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,django,blog.iohub.link', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'techblog_cms',  # Add the techblog_cms application
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'techblog_cms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'techblog_cms', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'techblog_cms.context_processors.testing_mode',
            ],
        },
    },
]

WSGI_APPLICATION = 'techblog_cms.wsgi.application'

# Database
# Detect testing mode either via explicit env var or when running under pytest
IS_TESTING = os.environ.get('TESTING') == 'True' or 'PYTEST_CURRENT_TEST' in os.environ or any(
    x.endswith('pytest') for x in sys.modules.keys()
)
print(f"IS_TESTING: {IS_TESTING}")

if IS_TESTING:
    # Testing uses SQLite for simplicity
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    # Disable CSRF for testing
    MIDDLEWARE = [m for m in MIDDLEWARE if m != 'django.middleware.csrf.CsrfViewMiddleware']
    DEBUG = True
    APPEND_SLASH = False
    print(f"MIDDLEWARE after removal: {MIDDLEWARE}")
else:
    # Prefer DATABASE_URL when provided (12factor style)
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        parsed = urlparse(db_url)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': parsed.path.lstrip('/') or os.environ.get('APP_DB_NAME') or os.environ.get('POSTGRES_DB', 'techblogdb'),
                'USER': unquote(parsed.username or os.environ.get('APP_DB_USER') or os.environ.get('POSTGRES_USER', 'techblog')),
                'PASSWORD': unquote(parsed.password or os.environ.get('APP_DB_PASSWORD') or os.environ.get('POSTGRES_PASSWORD', 'techblogpass')),
                'HOST': parsed.hostname or os.environ.get('POSTGRES_HOST', 'db'),
                'PORT': str(parsed.port or os.environ.get('POSTGRES_PORT', '5432')),
            }
        }
    elif os.environ.get('APP_DB_USER') or os.environ.get('APP_DB_NAME') or os.environ.get('APP_DB_PASSWORD'):
        # Next preference: dedicated app credentials if provided
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('APP_DB_NAME', os.environ.get('POSTGRES_DB', 'techblogdb')),
                'USER': os.environ.get('APP_DB_USER', os.environ.get('POSTGRES_USER', 'techblog')),
                'PASSWORD': os.environ.get('APP_DB_PASSWORD', os.environ.get('POSTGRES_PASSWORD', 'techblogpass')),
                'HOST': os.environ.get('POSTGRES_HOST', 'db'),
                'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            }
        }
    else:
        # Fallback to generic POSTGRES_* variables
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('POSTGRES_DB', 'techblogdb'),
                'USER': os.environ.get('POSTGRES_USER', 'techblog'),
                'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'techblogpass'),
                'HOST': os.environ.get('POSTGRES_HOST', 'db'),
                'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            }
        }

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'techblog_cms', 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Article asset tuning knobs (overridable via environment variables)
ARTICLE_IMAGE_MAX_BYTES = config('ARTICLE_IMAGE_MAX_BYTES', default=5 * 1024 * 1024, cast=int)
ARTICLE_IMAGE_ALLOWED_FORMATS = tuple(
    fmt.upper() for fmt in config('ARTICLE_IMAGE_ALLOWED_FORMATS', default='JPEG,PNG,GIF,WEBP', cast=Csv())
)
ARTICLE_IMAGE_MAX_PIXELS = config('ARTICLE_IMAGE_MAX_PIXELS', default=20_000_000, cast=int)

# Admin hardening
HIDE_ADMIN_URL = True

# CSRF failure view for debugging
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# Login URL
LOGIN_URL = '/login/'

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://blog.iohub.link',
    'http://blog.iohub.link',
    'https://localhost',
    'http://localhost',
    'https://127.0.0.1',
    'http://127.0.0.1',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Security Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF Settings
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'techblog',
        'TIMEOUT': 300,
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_NAME = 'techblog_sessionid'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'techblog_cms': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email configuration (for production)
if not DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@techblog.com')
    ADMINS = [('Admin', config('ADMIN_EMAIL', default='admin@techblog.com'))]

# Testing configuration
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
