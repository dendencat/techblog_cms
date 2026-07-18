import os
import sys

from django.core.cache import cache

from .models import Category, Tag


SIDEBAR_CACHE_TTL = 300

def testing_mode(request):
    """Add IS_TESTING variable to template context"""
    IS_TESTING = os.environ.get('TESTING') == 'True' or 'PYTEST_CURRENT_TEST' in os.environ or any(
        x.endswith('pytest') for x in sys.modules.keys()
    )
    return {'IS_TESTING': IS_TESTING}


def sidebar(request):
    categories = cache.get('sidebar:categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('sidebar:categories', categories, SIDEBAR_CACHE_TTL)

    tags = cache.get('sidebar:tags')
    if tags is None:
        tags = list(Tag.objects.all())
        cache.set('sidebar:tags', tags, SIDEBAR_CACHE_TTL)

    return {
        'categories': categories,
        'tags': tags,
    }
