from django.core.cache import cache

from .models import Category, Tag


SIDEBAR_CACHE_TTL = 300


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
