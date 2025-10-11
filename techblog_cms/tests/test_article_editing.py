import io
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

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
        self.media_override_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_override_dir)
        self.media_override = override_settings(MEDIA_ROOT=self.media_override_dir)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

        self.category = Category.objects.create(name="General", description="General articles")
        self.article = Article.objects.create(
            title="Original Title",
            content="Original content",
            category=self.category,
            published=False,
        )
        self.user = User.objects.create_user(username="editor", password="pass1234")

    def _make_image_file(self, format="PNG", size=(32, 32), color=(255, 0, 0)):
        buffer = io.BytesIO()
        with Image.new('RGB', size, color) as image:
            image.save(buffer, format=format)
        buffer.seek(0)
        content_type_map = {
            'JPEG': 'image/jpeg',
            'JPG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'WEBP': 'image/webp',
        }
        content_type = content_type_map.get(format.upper(), 'application/octet-stream')
        return SimpleUploadedFile(f"test.{format.lower()}", buffer.getvalue(), content_type=content_type)

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

    def test_upload_small_png_sets_article_image(self):
        self.client.login(username="editor", password="pass1234")
        url = reverse("article_edit", args=[self.article.slug])
        image_file = self._make_image_file(format="PNG", size=(16, 16))

        response = self.client.post(
            url,
            {
                "title": "Original Title",
                "content": "Updated body with image",
                "action": "save",
                "image": image_file,
            },
        )

        self.assertEqual(response.status_code, 302)
        refreshed = Article.objects.get(pk=self.article.pk)
        self.assertTrue(refreshed.image.name.startswith("articles/"))
        self.assertTrue(refreshed.image.name.endswith(".png"))

    def test_plain_text_upload_is_rejected(self):
        self.client.login(username="editor", password="pass1234")
        url = reverse("article_edit", args=[self.article.slug])
        fake_image = SimpleUploadedFile("fake.png", b"not an image", content_type="image/png")

        response = self.client.post(
            url,
            {
                "title": "Original Title",
                "content": "Attempt with fake image",
                "action": "save",
                "image": fake_image,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Uploaded file is not a valid image.")
        refreshed = Article.objects.get(pk=self.article.pk)
        self.assertFalse(refreshed.image)

    def test_oversized_image_upload_is_rejected(self):
        self.client.login(username="editor", password="pass1234")
        url = reverse("article_edit", args=[self.article.slug])
        big_image = self._make_image_file(format="PNG", size=(512, 512))

        with override_settings(ARTICLE_IMAGE_MAX_BYTES=200):
            response = self.client.post(
                url,
                {
                    "title": "Original Title",
                    "content": "Attempt with big image",
                    "action": "save",
                    "image": big_image,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Image exceeds the maximum allowed size")
        refreshed = Article.objects.get(pk=self.article.pk)
        self.assertFalse(refreshed.image)


class MarkdownRenderingTests(TestCase):
    def test_plain_urls_are_linkified(self):
        html = markdown_to_html("Check https://example.com for details")
        self.assertIn('<a href="https://example.com">https://example.com</a>', html)
