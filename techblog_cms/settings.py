import os
import sys
from pathlib import Path
from decouple import config, Csv

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
    # Disable CSRF for testing
    MIDDLEWARE = [m for m in MIDDLEWARE if m != 'django.middleware.csrf.CsrfViewMiddleware']
    DEBUG = True
    APPEND_SLASH = False
    print(f"MIDDLEWARE after removal: {MIDDLEWARE}")
else:
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

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'techblog_cms', 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Admin hardening
HIDE_ADMIN_URL = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'