from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from techblog_cms.models import Article, Category
from techblog_cms.templatetags.markdown_filter import markdown_to_html


class ArticleSlugTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="General", description="General articles")

    def test_slug_contains_hash_fragment(self):
        article = Article.objects.create(
            title="Example Post",
            content="Body",
            category=self.category,
            published=False,
        )
        self.assertRegex(article.slug, r"^example-post-[0-9a-f]{8}$")

    def test_duplicate_titles_generate_unique_slugs(self):
        first = Article.objects.create(
            title="Example Post",
            content="Body",
            category=self.category,
        )
        second = Article.objects.create(
            title="Example Post",
            content="Body",
            category=self.category,
        )
        self.assertNotEqual(first.slug, second.slug)


class ArticleEditingTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="General", description="General articles")
        self.article = Article.objects.create(
            title="Original Title",
            content="Original content",
            category=self.category,
            published=False,
        )
        self.user = User.objects.create_user(username="editor", password="pass1234")

    def test_edit_updates_content_and_preserves_slug(self):
        self.client.login(username="editor", password="pass1234")
        url = reverse("article_edit", args=[self.article.slug])
        response = self.client.post(
            url,
            {
                "title": "Original Title",
                "content": "Updated body with new info",
                "action": "publish",
            },
        )
        self.assertEqual(response.status_code, 302)

        refreshed = Article.objects.get(pk=self.article.pk)
        self.assertEqual(refreshed.content, "Updated body with new info")
        self.assertTrue(refreshed.published)
        self.assertEqual(refreshed.slug, self.article.slug)
        self.assertGreaterEqual(refreshed.updated_at, refreshed.created_at)

        detail_response = self.client.get(reverse("article_detail", args=[refreshed.slug]))
        self.assertContains(detail_response, "Updated body with new info")
        self.assertContains(detail_response, "Updated:")


class MarkdownRenderingTests(TestCase):
    def test_plain_urls_are_linkified(self):
        html = markdown_to_html("Check https://example.com for details")
        self.assertIn('<a href="https://example.com">https://example.com</a>', html)
