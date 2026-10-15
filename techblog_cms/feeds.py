from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import Article, Category, Tag


class LatestArticlesFeed(Feed):
    description_template = None

    def title(self):
        return settings.BLOG_TITLE

    def description(self):
        return settings.BLOG_DESCRIPTION

    def link(self):
        return reverse('home')

    def items(self):
        return (
            Article.objects.public()
            .select_related('category')
            .prefetch_related('tags')
            .order_by('-published_at', '-created_at')[:20]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary

    def item_pubdate(self, item):
        return item.display_date

    def item_updateddate(self, item):
        return item.updated_at

    def item_categories(self, item):
        return [item.category.name] + [tag.name for tag in item.tags.all()]


class ArticleSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Article.objects.public().order_by('-published_at')

    def lastmod(self, item):
        return item.updated_at


class TaxonomySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.4

    def items(self):
        return list(Category.objects.all()) + list(Tag.objects.all())


class StaticSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['home', 'article_list', 'categories', 'tags']

    def location(self, item):
        return reverse(item)


SITEMAPS = {
    'static': StaticSitemap,
    'articles': ArticleSitemap,
    'taxonomies': TaxonomySitemap,
}
