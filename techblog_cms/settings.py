import os
import sys
import logging
from pathlib import Path
from decouple import config, Csv
from urllib.parse import urlparse, unquote

# Set up logging
logger = logging.getLogger(__name__)

# Detect testing mode early so dependent settings can branch consistently.
IS_TESTING = (
    os.environ.get('TESTING') == 'True'
    or 'PYTEST_CURRENT_TEST' in os.environ
    or any(name.endswith('pytest') for name in sys.modules)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# Check if SECRET_KEY is set
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. Please set a secure secret key.")

# Fallback for development (but warn)
if SECRET_KEY == 'django-insecure-default-key':
    import warnings
    warnings.warn("Using insecure default SECRET_KEY. Set SECRET_KEY environment variable for production.")

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
    'csp',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'csp.middleware.CSPMiddleware',
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

if IS_TESTING:
    # Unit tests use an in-memory SQLite database to avoid external service dependencies.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
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
# NOTE: Must start with a leading slash to avoid relative URLs like
# /dashboard/static/...  which break behind reverse proxy.
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'techblog_cms', 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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

# HTTPS and Security Settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookie Security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# Password Hashers
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "https://blog.iohub.link",
    "http://localhost:3000",  # For development
    "http://127.0.0.1:3000",  # For development
]

# CSP Settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
