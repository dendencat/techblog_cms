"""Tests for the editor / dashboard / reader improvements (publishing states, metadata,
image handling, search, feeds)."""
import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from techblog_cms.models import Article, ArticleInlineImage, Category, Tag
from techblog_cms.templatetags.markdown_filter import extract_toc, markdown_to_html


def make_png(name='image.png', size=(16, 16), color=(255, 0, 0)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class MediaRootMixin:
    def setUp(self):
        super().setUp()
        cache.clear()
        media_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_dir)
        override = override_settings(MEDIA_ROOT=media_dir)
        override.enable()
        self.addCleanup(override.disable)
        self.user = User.objects.create_user(username='editor', password='pass1234')
        self.category = Category.objects.create(name='General', slug='general')


class PublishingStateTests(MediaRootMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='editor', password='pass1234')

    def _post(self, article=None, **data):
        url = reverse('article_edit', args=[article.slug]) if article else reverse('article_new')
        payload = {'title': 'Title', 'content': 'Body', 'action': 'save'}
        payload.update(data)
        return self.client.post(url, payload)

    def test_new_article_saved_as_draft_stays_in_editor(self):
        response = self._post(title='Draft post')
        article = Article.objects.get(title='Draft post')
        self.assertRedirects(response, reverse('article_edit', args=[article.slug]))
        self.assertFalse(article.published)
        self.assertEqual(article.status, Article.STATUS_DRAFT)

    def test_save_on_published_article_keeps_it_published(self):
        article = Article.objects.create(title='Live', content='Body', category=self.category, published=True)
        self._post(article, title='Live', content='Edited', action='save')
        article.refresh_from_db()
        self.assertTrue(article.published)
        self.assertEqual(article.content, 'Edited')

    def test_unpublish_returns_article_to_draft(self):
        article = Article.objects.create(title='Live', content='Body', category=self.category, published=True)
        self._post(article, title='Live', action='unpublish')
        article.refresh_from_db()
        self.assertFalse(article.published)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('article_detail', args=[article.slug])).status_code, 404)

    def test_publish_sets_publication_date(self):
        response = self._post(title='Now', action='publish')
        article = Article.objects.get(title='Now')
        self.assertTrue(article.is_public)
        self.assertIsNotNone(article.published_at)
        self.assertEqual(response.status_code, 302)

    def test_future_publication_date_schedules_the_article(self):
        future = timezone.localtime(timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
        self._post(title='Later', action='publish', published_at=future)
        article = Article.objects.get(title='Later')
        self.assertEqual(article.status, Article.STATUS_SCHEDULED)

        self.client.logout()
        self.assertEqual(self.client.get(reverse('article_detail', args=[article.slug])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('article_list')), 'Later')
        self.assertNotContains(self.client.get(reverse('feed')), 'Later')

    def test_invalid_publication_date_is_reported(self):
        response = self._post(title='Bad date', published_at='not-a-date')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '公開日時の形式が正しくありません')
        self.assertFalse(Article.objects.filter(title='Bad date').exists())


class EditorMetadataTests(MediaRootMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='editor', password='pass1234')

    def test_category_tags_excerpt_and_slug_are_saved(self):
        infra = Category.objects.create(name='Infra', slug='infra')
        Tag.objects.create(name='Docker', slug='docker')
        self.client.post(reverse('article_new'), {
            'title': 'Meta',
            'content': 'Body',
            'category': infra.pk,
            'tags': 'docker, 機械学習、Python',
            'excerpt': 'Short summary',
            'slug': 'my-meta-post',
            'action': 'save',
        })
        article = Article.objects.get(title='Meta')
        self.assertEqual(article.category, infra)
        self.assertEqual(article.slug, 'my-meta-post')
        self.assertEqual(article.excerpt, 'Short summary')
        names = sorted(tag.name for tag in article.tags.all())
        # Existing tag is reused case-insensitively; new ones are created.
        self.assertEqual(names, ['Docker', 'Python', '機械学習'])
        self.assertEqual(Tag.objects.filter(name__iexact='docker').count(), 1)

    def test_new_category_can_be_created_from_the_editor(self):
        self.client.post(reverse('article_new'), {
            'title': 'New cat', 'content': 'Body', 'new_category': 'Kubernetes', 'action': 'save',
        })
        article = Article.objects.get(title='New cat')
        self.assertEqual(article.category.name, 'Kubernetes')
        self.assertEqual(article.category.slug, 'kubernetes')

    def test_non_ascii_tag_names_get_routable_unique_slugs(self):
        first = Tag.objects.create(name='機械学習')
        second = Tag.objects.create(name='自然言語処理')
        self.assertRegex(first.slug, r'^tag-[0-9a-f]{8}$')
        self.assertNotEqual(first.slug, second.slug)
        self.assertEqual(self.client.get(first.get_absolute_url()).status_code, 200)

    def test_fields_missing_from_post_keep_stored_values(self):
        infra = Category.objects.create(name='Infra', slug='infra')
        article = Article.objects.create(title='Keep', content='x', excerpt='Kept', category=infra)
        article.tags.add(Tag.objects.create(name='kept-tag'))
        self.client.post(reverse('article_edit', args=[article.slug]), {
            'title': 'Keep', 'content': 'changed', 'action': 'save',
        })
        article.refresh_from_db()
        self.assertEqual(article.content, 'changed')
        self.assertEqual(article.category, infra)
        self.assertEqual(article.excerpt, 'Kept')
        self.assertEqual([tag.name for tag in article.tags.all()], ['kept-tag'])

    def test_duplicate_slug_is_rejected(self):
        Article.objects.create(title='Taken', slug='taken', content='x', category=self.category)
        response = self.client.post(reverse('article_new'), {
            'title': 'Other', 'content': 'Body', 'slug': 'taken', 'action': 'save',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'このスラッグは既に使われています')

    def test_editor_redisplays_submitted_values_on_error(self):
        response = self.client.post(reverse('article_new'), {
            'title': '', 'content': 'Keep me', 'tags': 'keep-tag', 'action': 'save',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Keep me')
        self.assertContains(response, 'keep-tag')


class SummaryAndTocTests(TestCase):
    def test_summary_is_plain_text_without_markdown_or_code(self):
        category = Category.objects.create(name='General', slug='general')
        article = Article.objects.create(
            title='T', category=category,
            content='## はじめに\n\n**大事**な話です。\n\n```python\nprint("secret")\n```\n\n- 項目',
        )
        self.assertEqual(article.excerpt, '')
        self.assertNotIn('##', article.summary)
        self.assertNotIn('**', article.summary)
        self.assertNotIn('print', article.summary)
        self.assertIn('大事な話です。', article.summary)

    def test_toc_lists_h2_and_h3_with_unicode_ids(self):
        html = markdown_to_html('## はじめに\n\ntext\n\n### 詳細\n\n## まとめ')
        toc = extract_toc(html)
        self.assertEqual([entry['text'] for entry in toc], ['はじめに', '詳細', 'まとめ'])
        self.assertEqual(toc[1]['level'], 3)
        self.assertIn(f'id="{toc[0]["id"]}"', html)


class InlineImageTests(MediaRootMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='editor', password='pass1234')

    def test_same_filename_in_two_articles_resolves_to_each_articles_image(self):
        first = Article.objects.create(title='A', content='![x](shot.png)', category=self.category, published=True)
        second = Article.objects.create(title='B', content='![x](shot.png)', category=self.category, published=True)
        first_image = ArticleInlineImage(article=first)
        first_image.image.save('shot.png', make_png(color=(255, 0, 0)), save=True)
        second_image = ArticleInlineImage(article=second)
        second_image.image.save('shot.png', make_png(color=(0, 0, 255)), save=True)
        self.assertNotEqual(first_image.image.url, second_image.image.url)

        response = self.client.get(reverse('article_detail', args=[second.slug]))
        self.assertContains(response, second_image.image.url)
        self.assertNotContains(response, first_image.image.url)

    def test_upload_api_returns_markdown_path(self):
        article = Article.objects.create(title='A', content='x', category=self.category)
        response = self.client.post(reverse('inline_image_upload'), {'image': make_png('diagram.png'), 'article': article.slug})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['filename'], 'diagram.png')
        self.assertTrue(data['markdown_path'].startswith('articles/'))
        self.assertEqual(ArticleInlineImage.objects.get(pk=data['id']).article, article)

        html = self.client.post(reverse('preview_markdown'), {'text': f"![d]({data['markdown_path']})"}).json()['html']
        self.assertIn(data['url'], html)

    def test_upload_api_rejects_non_images(self):
        fake = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        response = self.client.post(reverse('inline_image_upload'), {'image': fake})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertFalse(ArticleInlineImage.objects.exists())

    def test_upload_api_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse('inline_image_upload'), {'image': make_png()})
        self.assertEqual(response.status_code, 302)

    def test_images_uploaded_before_first_save_are_attached(self):
        upload = self.client.post(reverse('inline_image_upload'), {'image': make_png('early.png')}).json()
        self.assertIsNone(ArticleInlineImage.objects.get(pk=upload['id']).article)
        self.client.post(reverse('article_new'), {
            'title': 'With early image', 'content': f"![e]({upload['markdown_path']})",
            'inline_image_ids': [upload['id']], 'action': 'save',
        })
        article = Article.objects.get(title='With early image')
        self.assertEqual(ArticleInlineImage.objects.get(pk=upload['id']).article, article)

    def test_delete_api_removes_image(self):
        upload = self.client.post(reverse('inline_image_upload'), {'image': make_png()}).json()
        response = self.client.post(reverse('inline_image_delete', args=[upload['id']]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ArticleInlineImage.objects.filter(pk=upload['id']).exists())

    def test_cover_image_can_be_set_and_removed(self):
        article = Article.objects.create(title='Cover', content='x', category=self.category)
        url = reverse('article_edit', args=[article.slug])
        self.client.post(url, {'title': 'Cover', 'content': 'x', 'cover_image': make_png('cover.png'), 'action': 'save'})
        article.refresh_from_db()
        self.assertTrue(article.image)
        self.client.post(url, {'title': 'Cover', 'content': 'x', 'remove_cover_image': '1', 'action': 'save'})
        article.refresh_from_db()
        self.assertFalse(article.image)


class ReaderFeatureTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name='General', slug='general')
        self.public = Article.objects.create(
            title='Kubernetes 入門', content='## 準備\n\nkubectl を使う\n\n## 実践\n\n本番', category=self.category, published=True,
        )
        self.draft = Article.objects.create(title='Kubernetes 下書き', content='kubectl', category=self.category)

    def test_search_finds_public_articles_only(self):
        response = self.client.get(reverse('search'), {'q': 'kubectl'})
        self.assertContains(response, 'Kubernetes 入門')
        self.assertNotContains(response, 'Kubernetes 下書き')

    def test_empty_search_renders_form(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)

    def test_detail_shows_table_of_contents(self):
        response = self.client.get(reverse('article_detail', args=[self.public.slug]))
        self.assertContains(response, '目次')
        self.assertEqual([entry['text'] for entry in response.context['toc']], ['準備', '実践'])

    def test_feed_sitemap_and_robots(self):
        feed = self.client.get(reverse('feed'))
        self.assertEqual(feed.status_code, 200)
        self.assertContains(feed, 'Kubernetes 入門')
        self.assertNotContains(feed, '下書き')

        sitemap = self.client.get(reverse('sitemap'))
        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, self.public.get_absolute_url())
        self.assertNotContains(sitemap, self.draft.get_absolute_url())

        robots = self.client.get(reverse('robots'))
        self.assertContains(robots, 'Sitemap:')

    def test_logged_in_author_sees_draft_preview_banner(self):
        User.objects.create_user(username='editor', password='pass1234')
        self.client.login(username='editor', password='pass1234')
        response = self.client.get(reverse('article_detail', args=[self.draft.slug]))
        self.assertContains(response, '下書き</strong>のプレビュー')


class DashboardTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username='editor', password='pass1234')
        self.client.login(username='editor', password='pass1234')
        category = Category.objects.create(name='General', slug='general')
        Article.objects.create(title='Live one', content='x', category=category, published=True)
        Article.objects.create(title='Draft one', content='x', category=category)
        Article.objects.create(
            title='Scheduled one', content='x', category=category, published=True,
            published_at=timezone.now() + timedelta(days=1),
        )

    def test_status_filter(self):
        for status, expected, hidden in (
            ('draft', 'Draft one', 'Live one'),
            ('published', 'Live one', 'Scheduled one'),
            ('scheduled', 'Scheduled one', 'Draft one'),
        ):
            with self.subTest(status=status):
                response = self.client.get(reverse('dashboard'), {'status': status})
                self.assertContains(response, expected)
                self.assertNotContains(response, hidden)

    def test_search_and_tab_counts(self):
        response = self.client.get(reverse('dashboard'), {'q': 'Draft'})
        self.assertContains(response, 'Draft one')
        self.assertNotContains(response, 'Live one')
        counts = {tab['key']: tab['count'] for tab in response.context['status_tabs']}
        self.assertEqual(counts, {'all': 1, 'published': 0, 'scheduled': 0, 'draft': 1})

    def test_delete_redirects_to_dashboard_with_message(self):
        article = Article.objects.get(title='Draft one')
        response = self.client.post(reverse('article_delete', args=[article.slug]), follow=True)
        self.assertRedirects(response, reverse('dashboard'))
        self.assertContains(response, '「Draft one」を削除しました')


class LoginRedirectTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='editor', password='pass1234')

    def test_login_honours_safe_next(self):
        response = self.client.post(reverse('login'), {
            'username': 'editor', 'password': 'pass1234', 'next': '/dashboard/articles/new/',
        })
        self.assertRedirects(response, '/dashboard/articles/new/', fetch_redirect_response=False)

    def test_login_ignores_external_next(self):
        response = self.client.post(reverse('login'), {
            'username': 'editor', 'password': 'pass1234', 'next': 'https://evil.example/',
        })
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
