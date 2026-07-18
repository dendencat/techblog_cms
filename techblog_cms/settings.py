import logging
import os
import sys
from pathlib import Path
from decouple import config, Csv
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS configuration
# ALLOWED_HOSTS configuration
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,django,blog.iohub.link', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'techblog_cms.apps.TechblogCmsConfig',
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
                'techblog_cms.context_processors.sidebar',
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
logger.debug("IS_TESTING: %s", IS_TESTING)

if IS_TESTING:
    # Tests default to SQLite for speed; set TEST_DB_ENGINE=postgres (as CI
    # does) to run them against the same engine as production.
    if os.environ.get('TEST_DB_ENGINE') == 'postgres':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('POSTGRES_DB', 'techblogdb'),
                'USER': os.environ.get('POSTGRES_USER', 'techblog'),
                'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'techblogpass'),
                'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
                'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'techblog-test-cache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    DEBUG = True
    APPEND_SLASH = False
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

DATABASES['default']['CONN_MAX_AGE'] = config('CONN_MAX_AGE', default=60, cast=int)

if not DEBUG:
    TEMPLATES[0]['APP_DIRS'] = False
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        (
            'django.template.loaders.cached.Loader',
            [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        ),
    ]

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
ARTICLE_IMAGE_MAX_DIMENSION = config('ARTICLE_IMAGE_MAX_DIMENSION', default=1920, cast=int)

# CSRF failure view for debugging
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# Login URL
LOGIN_URL = '/login/'

# CSRF trusted origins
DEFAULT_CSRF_TRUSTED_ORIGINS = (
    'https://blog.iohub.link',
    'http://blog.iohub.link',
    'https://localhost',
    'http://localhost',
    'https://127.0.0.1',
    'http://127.0.0.1',
)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default=','.join(DEFAULT_CSRF_TRUSTED_ORIGINS),
    cast=Csv(),
)

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
    SECURE_REDIRECT_EXEMPT = [r'^health/$', r'^ready/$']
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

# Cache Configuration
if not IS_TESTING:
    redis_url = config('REDIS_URL', default='redis://redis:6379/1')
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'techblog',
            'TIMEOUT': 300,
        }
    }
    redis_password = config('REDIS_PASSWORD', default='')
    parsed_redis_url = urlparse(redis_url)
    if redis_password and parsed_redis_url.username is None and parsed_redis_url.password is None:
        CACHES['default']['OPTIONS']['PASSWORD'] = redis_password

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
            'filename': str(LOG_DIR / 'django.log'),
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
