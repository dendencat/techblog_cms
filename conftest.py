import pytest
from django.conf import settings

def pytest_configure():
    """Configure Django settings for tests"""
    settings.DEBUG = False
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    }
    settings.ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', 'blog.iohub.link']
    settings.MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]

@pytest.fixture(autouse=True)
def db_setup(db):
    """Set up database for tests"""
    pass
