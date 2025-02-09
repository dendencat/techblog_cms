import os
import pytest
from django.conf import settings

@pytest.fixture(scope='session')
def django_db_setup():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'techblogdb'),
        'USER': os.environ.get('POSTGRES_USER', 'techblog'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'techblogpass'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
