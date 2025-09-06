import os
import pytest
import django
from django.conf import settings

def pytest_configure():
    """Configure Django settings for tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techblog_cms.settings')
    os.environ['TESTING'] = 'True'
    django.setup()
    
    # Override settings for tests
    settings.DEBUG = False  # Match production expectation
    settings.ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', 'blog.iohub.link']
    settings.MIDDLEWARE = [
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
    settings.SECRET_KEY = 'test-key'

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        pass

@pytest.fixture(scope='session')
def django_settings():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techblog_cms.settings')
    os.environ['DEBUG'] = 'True'
    os.environ['SECRET_KEY'] = 'test-key'
    os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,testserver'

@pytest.fixture(autouse=True)
def db_setup(db):
    """Set up database for tests"""
    pass
