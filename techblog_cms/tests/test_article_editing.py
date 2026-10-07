import io
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from techblog_cms.models import Article, Category, ArticleInlineImage
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

    def _make_image_file(self, format="PNG", size=(32, 32), color=(255, 0, 0), name=None):
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
        filename = name or f"test.{format.lower()}"
        return SimpleUploadedFile(filename, buffer.getvalue(), content_type=content_type)

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

    def test_uploading_multiple_images_creates_inline_images(self):
        self.client.login(username="editor", password="pass1234")
        url = reverse("article_edit", args=[self.article.slug])
        image_one = self._make_image_file(format="PNG", size=(32, 32), name="diagram.png")
        image_two = self._make_image_file(format="PNG", size=(24, 24), color=(0, 255, 0), name="diagram-2.png")

        response = self.client.post(
            url,
            {
                "title": "Original Title",
                "content": "Updated body with image\n\n![first](diagram.png)\n![second](diagram-2.png)",
                "action": "save",
                "images": [image_one, image_two],
            },
        )

        self.assertEqual(response.status_code, 302)
        refreshed = Article.objects.get(pk=self.article.pk)
        self.assertFalse(refreshed.image)

        attachments = ArticleInlineImage.objects.filter(article=refreshed).order_by('uploaded_at')
        self.assertEqual(attachments.count(), 2)
        filenames = {attachment.filename for attachment in attachments}
        self.assertIn("diagram.png", filenames)
        self.assertIn("diagram-2.png", filenames)

        detail_response = self.client.get(reverse("article_detail", args=[refreshed.slug]))
        for attachment in attachments:
            self.assertContains(detail_response, attachment.image.url)

    def test_inline_image_long_edge_is_resized(self):
        self.client.login(username="editor", password="pass1234")
        url = reverse("article_edit", args=[self.article.slug])
        large_image = self._make_image_file(
            format="PNG",
            size=(1200, 2400),
            name="portrait.png",
        )

        response = self.client.post(
            url,
            {
                "title": "Original Title",
                "content": "Updated body with an inline image",
                "action": "save",
                "images": [large_image],
            },
        )

        self.assertEqual(response.status_code, 302)
        attachment = ArticleInlineImage.objects.get(article=self.article)
        self.assertEqual(attachment.filename, "portrait.png")
        with Image.open(attachment.image.path) as saved_image:
            self.assertEqual(saved_image.size, (960, 1920))
            self.assertEqual(saved_image.format, "PNG")

    def test_gif_upload_is_saved_without_reencoding(self):
        self.client.login(username="editor", password="pass1234")
        url = reverse("article_edit", args=[self.article.slug])
        buffer = io.BytesIO()
        frames = [
            Image.new("RGB", (32, 32), (255, 0, 0)),
            Image.new("RGB", (32, 32), (0, 0, 255)),
        ]
        frames[0].save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
        )
        original_bytes = buffer.getvalue()
        animated_gif = SimpleUploadedFile(
            "animation.gif",
            original_bytes,
            content_type="image/gif",
        )

        response = self.client.post(
            url,
            {
                "title": "Original Title",
                "content": "Updated body with an animation",
                "action": "save",
                "images": [animated_gif],
            },
        )

        self.assertEqual(response.status_code, 302)
        attachment = ArticleInlineImage.objects.get(article=self.article)
        with attachment.image.open("rb") as saved_gif:
            self.assertEqual(saved_gif.read(), original_bytes)

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
                "images": [fake_image],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Uploaded file is not a valid image.")
        refreshed = Article.objects.get(pk=self.article.pk)
        self.assertFalse(refreshed.image)
        self.assertFalse(ArticleInlineImage.objects.filter(article=refreshed).exists())

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
                    "images": [big_image],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Image exceeds the maximum allowed size")
        refreshed = Article.objects.get(pk=self.article.pk)
        self.assertFalse(refreshed.image)
        self.assertFalse(ArticleInlineImage.objects.filter(article=refreshed).exists())


class MarkdownRenderingTests(TestCase):
    def test_plain_urls_are_linkified(self):
        html = markdown_to_html("Check https://example.com for details")
        self.assertIn('<a href="https://example.com">https://example.com</a>', html)

    def test_relative_image_paths_use_media_url(self):
        with override_settings(MEDIA_URL='/media/'):
            html = markdown_to_html("![Infra diagram](diagram.png)")
        self.assertIn('src="/media/articles/diagram.png"', html)

    def test_articles_prefixed_image_paths_are_preserved(self):
        with override_settings(MEDIA_URL='/media/'):
            html = markdown_to_html("![Infra diagram](articles/diagram.png)")
        self.assertIn('src="/media/articles/diagram.png"', html)
