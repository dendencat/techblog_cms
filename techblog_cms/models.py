import uuid
from pathlib import Path
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse


def unique_slug(model, value, *, exclude_pk=None, fallback='item', max_length=50):
    """Return an ASCII slug for ``value`` that is unique for ``model``.

    Non-ASCII names (e.g. Japanese tag names) slugify to an empty string, which
    would collide on the unique index and cannot be routed by ``<slug:...>``,
    so they fall back to ``<fallback>-<hash>``.
    """
    base = slugify(value or '')[:max_length - 9].strip('-')
    queryset = model.objects.exclude(pk=exclude_pk) if exclude_pk is not None else model.objects.all()
    candidate = base or f"{fallback}-{uuid.uuid4().hex[:8]}"
    while queryset.filter(slug=candidate).exists():
        candidate = f"{base or fallback}-{uuid.uuid4().hex[:8]}"
    return candidate


def article_image_upload_to(instance, filename):
    """Store every upload in its own directory so equal filenames never collide."""
    return f"articles/{uuid.uuid4().hex[:12]}/{Path(filename).name}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name, exclude_pk=self.pk, fallback='category')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category', kwargs={'slug': self.slug})

    def article_count(self):
        return self.article_set.count()

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Tag, self.name, exclude_pk=self.pk, fallback='tag')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', kwargs={'slug': self.slug})

    class Meta:
        ordering = ['name']


class ArticleQuerySet(models.QuerySet):
    def public(self):
        """Articles readers may see: published and not scheduled for the future."""
        return self.filter(published=True).filter(
            Q(published_at__isnull=True) | Q(published_at__lte=timezone.now())
        )


class Article(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_PUBLISHED = 'published'

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.ImageField(upload_to=article_image_upload_to, blank=True, null=True)

    objects = ArticleQuerySet.as_manager()

    def _generate_unique_slug(self):
        slug_field = self._meta.get_field('slug')
        max_length = slug_field.max_length or 50
        suffix_length = 8
        base_slug = slugify(self.title) or 'article'

        if max_length > suffix_length + 1:
            base_max_length = max_length - (suffix_length + 1)
            base_slug = base_slug[:base_max_length].rstrip('-')
            if not base_slug:
                base_slug = 'article'
            base_slug = base_slug[:base_max_length]
        else:
            base_slug = ''

        while True:
            if base_slug:
                hash_fragment = uuid.uuid4().hex[:suffix_length]
                candidate = f"{base_slug}-{hash_fragment}"
            else:
                candidate = uuid.uuid4().hex[:max_length]
            if not Article.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                return candidate

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        if self.published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'slug': self.slug})

    @property
    def status(self):
        if not self.published:
            return self.STATUS_DRAFT
        if self.published_at and self.published_at > timezone.now():
            return self.STATUS_SCHEDULED
        return self.STATUS_PUBLISHED

    @property
    def is_public(self):
        return self.status == self.STATUS_PUBLISHED

    @property
    def display_date(self):
        return self.published_at or self.created_at

    @property
    def was_updated(self):
        """True when the article was edited on a later day than it went out."""
        return timezone.localdate(self.updated_at) > timezone.localdate(self.display_date)

    @property
    def summary(self):
        """Plain-text summary: the hand-written excerpt, else the start of the body."""
        if self.excerpt:
            return self.excerpt
        from techblog_cms.templatetags.markdown_filter import markdown_to_plain_text
        return markdown_to_plain_text(self.content, max_length=160)

    @property
    def reading_minutes(self):
        from techblog_cms.templatetags.markdown_filter import markdown_to_plain_text
        # ~500 Japanese characters per minute is the commonly used reading speed.
        return max(1, round(len(markdown_to_plain_text(self.content)) / 500))

    class Meta:
        indexes = [
            models.Index(
                fields=['published', '-created_at'],
                name='article_pub_created_idx',
            ),
        ]


class ArticleInlineImage(models.Model):
    # Nullable so images can be uploaded from the editor before a new article is first saved;
    # the editor attaches them to the article on save.
    article = models.ForeignKey(
        Article, related_name='inline_images', on_delete=models.CASCADE, null=True, blank=True,
    )
    image = models.ImageField(upload_to=article_image_upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at', 'pk']

    @property
    def filename(self):
        return Path(self.image.name or '').name

    @property
    def markdown_path(self):
        """Path to reference this image from Markdown, unambiguous across articles."""
        return self.image.name or ''

    def __str__(self):
        return self.filename or f"Inline image #{self.pk}"
