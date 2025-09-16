import uuid
from django.db import models
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category', kwargs={'slug': self.slug})

    def article_count(self):
        return self.article_set.count()

    class Meta:
        verbose_name_plural = "categories"

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', kwargs={'slug': self.slug})

class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.ImageField(upload_to='articles/', blank=True, null=True)

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
        if not self.excerpt and self.content:
            self.excerpt = self.content[:200]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'slug': self.slug})
