from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.safestring import mark_safe

from techblog_cms.models import Article, Category, Tag

class HomePageTests(TestCase):
    def test_home_page_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_content(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Welcome to Tech Blog')


class SidebarContextProcessorTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_home_sidebar_displays_cached_categories_and_tags(self):
        category = Category.objects.create(name='Caching', slug='caching')
        tag = Tag.objects.create(name='Redis', slug='redis')

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, category.name)
        self.assertContains(response, tag.name)
        self.assertIsInstance(response.context['categories'], list)
        self.assertIsInstance(response.context['tags'], list)

    def test_sidebar_cache_is_invalidated_when_category_is_created(self):
        self.client.get(reverse('home'))
        category = Category.objects.create(name='Signals', slug='signals')

        response = self.client.get(reverse('home'))

        self.assertContains(response, category.name)


class PublicArticleViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name='Performance', slug='performance')
        self.tag = Tag.objects.create(name='Django', slug='django')
        for number in range(12):
            article = Article.objects.create(
                title=f'Published article {number}',
                content=f'Content {number}',
                category=self.category,
                published=True,
            )
            article.tags.add(self.tag)

        self.draft = Article.objects.create(
            title='Unpublished draft',
            content='Draft content',
            category=self.category,
            published=False,
        )

    def test_paginated_article_views_return_second_page(self):
        urls = (
            reverse('article_list'),
            reverse('category', args=[self.category.slug]),
            reverse('tag', args=[self.tag.slug]),
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url, {'page': 2})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['page_obj'].number, 2)
                self.assertEqual(len(response.context['articles']), 2)

    def test_category_list_count_includes_unpublished_articles(self):
        response = self.client.get(reverse('categories'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '13 articles')

    def test_article_detail_renders_and_caches_content_html(self):
        article = Article.objects.filter(published=True).first()
        rendered_html = mark_safe('<h2>Rendered content</h2>')

        with patch('techblog_cms.views.markdown_to_html', return_value=rendered_html) as renderer:
            first_response = self.client.get(reverse('article_detail', args=[article.slug]))
            second_response = self.client.get(reverse('article_detail', args=[article.slug]))

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.context['content_html'], rendered_html)
        self.assertContains(first_response, rendered_html, html=True)
        self.assertEqual(second_response.status_code, 200)
        renderer.assert_called_once_with(article.content)
