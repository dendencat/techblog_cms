from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Tag


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_sidebar_cache(**kwargs):
    cache.delete('sidebar:categories')


@receiver([post_save, post_delete], sender=Tag)
def invalidate_tag_sidebar_cache(**kwargs):
    cache.delete('sidebar:tags')
