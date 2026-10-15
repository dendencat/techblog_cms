import io
import re
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from PIL import Image, ImageOps, UnidentifiedImageError
from .models import Article, Category, Tag, ArticleInlineImage
from techblog_cms.templatetags.markdown_filter import (
    bind_inline_images,
    extract_toc,
    markdown_to_html,
)
from django.conf import settings
from django.http import HttpResponseNotFound

PUBLIC_PAGE_SIZE = 10
LOGIN_ERROR_MESSAGE = 'Invalid credentials'
SLUG_PATTERN = re.compile(r'^[-a-zA-Z0-9_]+$')
TAG_SPLIT_PATTERN = re.compile(r'[,、，]')


def _public_articles():
    return (
        Article.objects.public()
        .select_related('category')
        .prefetch_related('tags')
        .order_by(F('published_at').desc(nulls_last=True), '-created_at')
    )


def _public_count_filter(prefix='article'):
    now = timezone.now()
    return Q(**{f'{prefix}__published': True}) & (
        Q(**{f'{prefix}__published_at__isnull': True}) | Q(**{f'{prefix}__published_at__lte': now})
    )


def _paginate(request, queryset, per_page=PUBLIC_PAGE_SIZE):
    return Paginator(queryset, per_page).get_page(request.GET.get('page', 1))


def home_view(request):
    return render(
        request,
        'home.html',
        {
            'articles': _public_articles()[:PUBLIC_PAGE_SIZE],
        },
    )

def article_list_view(request):
    page_obj = _paginate(request, _public_articles())
    return render(
        request,
        'article_list.html',
        {
            'articles': page_obj,
            'page_obj': page_obj,
        },
    )

def categories_view(request):
    categories = Category.objects.annotate(num_articles=Count('article', filter=_public_count_filter()))
    return render(
        request,
        'category_list.html',
        {
            'category_list': categories,
        },
    )

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    page_obj = _paginate(request, _public_articles().filter(category=category))
    return render(
        request,
        'category_detail.html',
        {
            'category': category,
            'articles': page_obj,
            'page_obj': page_obj,
        },
    )

def tags_view(request):
    tag_list = (
        Tag.objects.annotate(num_articles=Count('article', filter=_public_count_filter()))
        .order_by('-num_articles', 'name')
    )
    return render(request, 'tag_list.html', {'tag_list': tag_list})

def tag_view(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    page_obj = _paginate(request, _public_articles().filter(tags=tag))
    return render(
        request,
        'tag_detail.html',
        {
            'tag': tag,
            'articles': page_obj,
            'page_obj': page_obj,
        },
    )


def search_view(request):
    query = (request.GET.get('q') or '').strip()[:100]
    page_obj = None
    if query:
        matches = _public_articles().filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(tags__name__iexact=query)
            | Q(category__name__iexact=query)
        ).distinct()
        page_obj = _paginate(request, matches)
    return render(
        request,
        'search.html',
        {
            'query': query,
            'articles': page_obj or [],
            'page_obj': page_obj,
        },
    )


def article_detail_view(request, slug):
    articles = Article.objects.select_related('category').prefetch_related('tags', 'inline_images')
    # ログインしている場合は下書き・予約記事もプレビューできる
    if request.user.is_authenticated:
        article = get_object_or_404(articles, slug=slug)
    else:
        article = get_object_or_404(articles.public(), slug=slug)
    # v3: headings gained permalink anchors and Unicode ids
    cache_key = f'article_html:v3:{article.pk}:{article.updated_at.isoformat()}'
    content_html = cache.get(cache_key)
    if content_html is None:
        content_html = str(markdown_to_html(article.content))
        cache.set(cache_key, content_html, timeout=60 * 60 * 24)
    content_html = bind_inline_images(content_html, article.inline_images.all())
    toc = extract_toc(content_html)

    related_articles = _public_articles().filter(category=article.category).exclude(pk=article.pk)[:3]
    return render(
        request,
        'article_detail.html',
        {
            'article': article,
            'content_html': mark_safe(content_html),
            'toc': toc if len(toc) >= 2 else [],
            'related_articles': related_articles,
        },
    )
def admin_guard(request):
    """Return 404 for all direct /admin/ access."""
    return HttpResponseNotFound('<h1>Not Found</h1>')


def validate_article_image(uploaded_file):
    """
    Validate uploaded article image and rewind the file ready for storage.

    Returns:
        tuple(UploadedFile|None, str|None): (clean_file, error_message)
    """
    if not uploaded_file:
        return None, None

    max_bytes = getattr(settings, 'ARTICLE_IMAGE_MAX_BYTES', None)
    allowed_formats = getattr(settings, 'ARTICLE_IMAGE_ALLOWED_FORMATS', ())
    max_pixels = getattr(settings, 'ARTICLE_IMAGE_MAX_PIXELS', None)

    if max_bytes and uploaded_file.size and uploaded_file.size > max_bytes:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass
        return None, f"Image exceeds the maximum allowed size of {max_bytes} bytes."

    try:
        uploaded_file.seek(0)
    except (AttributeError, OSError):
        pass

    try:
        with Image.open(uploaded_file) as image:
            image.verify()

        uploaded_file.seek(0)
        with Image.open(uploaded_file) as image:
            detected_format = (image.format or '').upper()
            width, height = image.size
    except Image.DecompressionBombError:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass
        return None, "Image exceeds the maximum allowed pixel count."
    except UnidentifiedImageError:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass
        return None, "Uploaded file is not a valid image."
    except OSError:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass
        return None, "Uploaded file could not be processed as an image."

    total_pixels = width * height
    if max_pixels and total_pixels > max_pixels:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass
        return None, f"Image exceeds the maximum allowed pixel count of {max_pixels}."

    if allowed_formats and detected_format not in allowed_formats:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass
        allowed_display = ", ".join(allowed_formats)
        return None, f"Unsupported image format. Allowed formats: {allowed_display}."

    try:
        uploaded_file.seek(0)
    except (AttributeError, OSError):
        pass

    return uploaded_file, None


def process_article_image(uploaded_file):
    """Normalize a validated article image while preserving its filename."""
    if not uploaded_file:
        return None

    original_name = uploaded_file.name
    uploaded_file.seek(0)

    with Image.open(uploaded_file) as image:
        image_format = (image.format or '').upper()
        if image_format == 'GIF':
            uploaded_file.seek(0)
            return uploaded_file

        processed_image = ImageOps.exif_transpose(image)
        max_dimension = settings.ARTICLE_IMAGE_MAX_DIMENSION
        if max_dimension and max(processed_image.size) > max_dimension:
            processed_image.thumbnail(
                (max_dimension, max_dimension),
                Image.Resampling.LANCZOS,
            )

        output = io.BytesIO()
        save_options = {'quality': 85} if image_format == 'JPEG' else {}
        processed_image.save(output, format=image_format, **save_options)

    return ContentFile(output.getvalue(), name=original_name)


def _clean_image(uploaded_file):
    """Validate and normalize one uploaded image. Returns (file, error_message)."""
    cleaned, error = validate_article_image(uploaded_file)
    if error:
        display_name = getattr(uploaded_file, 'name', '選択した画像')
        return None, f"{display_name}: {error}"
    return (process_article_image(cleaned) if cleaned else None), None


def _safe_next_url(request, default='dashboard'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return next_url
    return default


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's authenticate function but ensure consistent behavior
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(_safe_next_url(request))
        else:
            # Generic error message to prevent username enumeration
            return render(
                request,
                'login.html',
                {"error": LOGIN_ERROR_MESSAGE, "username": username or '', "next": request.POST.get('next', '')},
                status=401,
            )
    return render(request, 'login.html', {"next": request.GET.get('next', '')})


@require_http_methods(["POST"])
def logout_view(request):
    # POST only (with CSRF) so third-party pages cannot log users out via a link or <img>.
    logout(request)
    return redirect('login')


DASHBOARD_STATUSES = (
    ('all', 'すべて'),
    (Article.STATUS_PUBLISHED, '公開中'),
    (Article.STATUS_SCHEDULED, '予約'),
    (Article.STATUS_DRAFT, '下書き'),
)
PER_PAGE_OPTIONS = [5, 10, 15, 20]


def _filter_by_status(queryset, status):
    now = timezone.now()
    if status == Article.STATUS_DRAFT:
        return queryset.filter(published=False)
    if status == Article.STATUS_SCHEDULED:
        return queryset.filter(published=True, published_at__gt=now)
    if status == Article.STATUS_PUBLISHED:
        return queryset.public()
    return queryset


@login_required
def dashboard_view(request):
    page_number = request.GET.get('page', 1)
    try:
        per_page = int(request.GET.get('per_page', 10))
    except (ValueError, TypeError):
        per_page = 10
    if per_page not in PER_PAGE_OPTIONS:
        per_page = 10

    status = request.GET.get('status', 'all')
    if status not in dict(DASHBOARD_STATUSES):
        status = 'all'
    query = (request.GET.get('q') or '').strip()[:100]

    articles = Article.objects.select_related('category').prefetch_related('tags')
    if query:
        articles = articles.filter(Q(title__icontains=query) | Q(content__icontains=query))
    status_tabs = [
        {'key': key, 'label': label, 'count': _filter_by_status(articles, key).count()}
        for key, label in DASHBOARD_STATUSES
    ]
    articles = _filter_by_status(articles, status).order_by('-updated_at')

    paginator = Paginator(articles, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': PER_PAGE_OPTIONS,
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'status': status,
        'status_tabs': status_tabs,
        'query': query,
    }
    return render(request, 'dashboard.html', context)


@login_required
def article_delete_view(request, slug):
    article = get_object_or_404(Article, slug=slug)

    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f'「{title}」を削除しました。')
        return redirect('dashboard')

    return render(request, 'article_delete_confirm.html', {'article': article})

@login_required
def article_delete_success_view(request):
    # Kept for old bookmarks; deletion now reports back on the dashboard.
    return redirect('dashboard')


def _parse_local_datetime(value):
    """Parse an ``<input type="datetime-local">`` value in the site's time zone."""
    value = (value or '').strip()
    if not value:
        return None, None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None, '公開日時の形式が正しくありません。'
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed, None


def _format_local_datetime(value):
    if not value:
        return ''
    return timezone.localtime(value).strftime('%Y-%m-%dT%H:%M')


def _split_tag_names(raw):
    names = []
    seen = set()
    for name in TAG_SPLIT_PATTERN.split(raw or ''):
        name = name.strip().lstrip('#').strip()[:50]
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names


def _resolve_tags(names):
    tags = []
    for name in names:
        tag = Tag.objects.filter(name__iexact=name).first() or Tag.objects.create(name=name)
        tags.append(tag)
    return tags


def _default_category():
    category, _ = Category.objects.get_or_create(
        name='General',
        defaults={'description': 'General articles'},
    )
    return category


def _resolve_category(category_id, new_category_name):
    new_category_name = (new_category_name or '').strip()[:100]
    if new_category_name:
        return (
            Category.objects.filter(name__iexact=new_category_name).first()
            or Category.objects.create(name=new_category_name)
        )
    if category_id:
        category = Category.objects.filter(pk=category_id).first()
        if category:
            return category
    return _default_category()


def _editor_values(article):
    if not article:
        return {
            'title': '', 'content': '', 'excerpt': '', 'slug': '', 'category_id': '',
            'new_category': '', 'tags': '', 'published_at': '',
        }
    return {
        'title': article.title,
        'content': article.content,
        'excerpt': article.excerpt,
        'slug': article.slug,
        'category_id': str(article.category_id or ''),
        'new_category': '',
        'tags': ', '.join(tag.name for tag in article.tags.all()),
        'published_at': _format_local_datetime(article.published_at),
    }


def _render_editor(request, article, values, errors=None, status=200):
    inline_images = list(article.inline_images.order_by('uploaded_at')) if article else []
    pending_ids = [int(pk) for pk in request.POST.getlist('inline_image_ids') if str(pk).isdigit()]
    if pending_ids:
        inline_images += list(ArticleInlineImage.objects.filter(pk__in=pending_ids, article__isnull=True))
    image_help_text = (
        f"対応形式: {', '.join(settings.ARTICLE_IMAGE_ALLOWED_FORMATS)} / "
        f"最大 {settings.ARTICLE_IMAGE_MAX_BYTES // (1024 * 1024)}MB / "
        f"長辺 {settings.ARTICLE_IMAGE_MAX_DIMENSION}px を超える画像は自動で縮小されます"
    )
    return render(
        request,
        'article_editor.html',
        {
            "errors": errors or [],
            "article": article,
            "values": values,
            "categories": Category.objects.order_by('name'),
            "all_tags": Tag.objects.order_by('name'),
            "image_help_text": image_help_text,
            "inline_images": inline_images,
            "media_url": settings.MEDIA_URL,
        },
        status=status,
    )


@login_required
@require_http_methods(["GET", "POST"])
def article_editor_view(request, slug=None):
    article = get_object_or_404(Article, slug=slug) if slug else None

    if request.method != 'POST':
        return _render_editor(request, article, _editor_values(article))

    values = {
        'title': ' '.join((request.POST.get('title') or '').split())[:200],
        'content': (request.POST.get('content') or '').strip(),
        'excerpt': (request.POST.get('excerpt') or '').strip()[:300],
        'slug': (request.POST.get('slug') or '').strip(),
        'category_id': request.POST.get('category') or '',
        'new_category': (request.POST.get('new_category') or '').strip(),
        'tags': (request.POST.get('tags') or '').strip(),
        'published_at': (request.POST.get('published_at') or '').strip(),
    }
    action = request.POST.get('action') or 'save'  # 'save' | 'publish' | 'unpublish'
    errors = []

    # Images are validated first so a rejected upload never leaves a half-saved article.
    cleaned_images = []
    for uploaded_image in request.FILES.getlist('images'):
        cleaned_image, image_error = _clean_image(uploaded_image)
        if image_error:
            errors.append(image_error)
        elif cleaned_image:
            cleaned_images.append(cleaned_image)

    cover_image = None
    if request.FILES.get('cover_image'):
        cover_image, image_error = _clean_image(request.FILES['cover_image'])
        if image_error:
            errors.append(image_error)

    if not values['title'] or not values['content']:
        errors.append("タイトルと本文は必須です。")

    if values['slug']:
        if not SLUG_PATTERN.match(values['slug']) or len(values['slug']) > 50:
            errors.append("スラッグは半角英数字・ハイフン・アンダースコア（50文字以内）で入力してください。")
        elif Article.objects.filter(slug=values['slug']).exclude(pk=getattr(article, 'pk', None)).exists():
            errors.append("このスラッグは既に使われています。")

    published_at, date_error = _parse_local_datetime(values['published_at'])
    if date_error:
        errors.append(date_error)

    if errors:
        return _render_editor(request, article, values, errors)

    is_new = article is None
    if is_new:
        article = Article()
    was_published = article.published

    article.title = values['title']
    article.content = values['content']
    # Fields absent from the POST (older clients, scripts) keep their stored values.
    if 'excerpt' in request.POST:
        article.excerpt = values['excerpt']
    if is_new or 'category' in request.POST or values['new_category']:
        article.category = _resolve_category(values['category_id'], values['new_category'])
    if values['slug']:
        article.slug = values['slug']

    if published_at is not None:
        article.published_at = published_at
    elif not article.published:
        # A blank date on an unpublished article means "publish now" when it goes out.
        article.published_at = None

    if action == 'publish':
        article.published = True
    elif action == 'unpublish':
        article.published = False

    if cover_image is not None:
        if article.image:
            article.image.delete(save=False)
        article.image = cover_image
    elif request.POST.get('remove_cover_image') and article.image:
        article.image.delete(save=False)
        article.image = None

    article.save()
    if 'tags' in request.POST:
        article.tags.set(_resolve_tags(_split_tag_names(values['tags'])))

    for cleaned_image in cleaned_images:
        inline_image = ArticleInlineImage(article=article)
        inline_image.image.save(cleaned_image.name, cleaned_image, save=True)
    pending_ids = [int(pk) for pk in request.POST.getlist('inline_image_ids') if str(pk).isdigit()]
    if pending_ids:
        ArticleInlineImage.objects.filter(pk__in=pending_ids, article__isnull=True).update(article=article)

    status = article.status
    if action == 'unpublish':
        messages.success(request, "記事を非公開（下書き）に戻しました。")
    elif status == Article.STATUS_SCHEDULED:
        local = timezone.localtime(article.published_at)
        messages.success(request, f"{local:%Y/%m/%d %H:%M} に公開予約しました。")
    elif status == Article.STATUS_PUBLISHED and not was_published:
        messages.success(request, "記事を公開しました。")
    elif status == Article.STATUS_PUBLISHED:
        messages.success(request, "公開中の記事を更新しました。")
    else:
        messages.success(request, "下書きを保存しました。")

    return redirect('article_edit', slug=article.slug)


def _json_error(message, status=400):
    return JsonResponse({"error": message}, status=status)


@login_required
@require_http_methods(["POST"])
def inline_image_upload_view(request):
    """Upload one image from the editor (drag & drop / paste) and return its Markdown path."""
    uploaded = request.FILES.get('image')
    if not uploaded:
        return _json_error("画像ファイルが送信されていません。")
    cleaned, error = _clean_image(uploaded)
    if error:
        return _json_error(error)

    article = None
    article_slug = request.POST.get('article')
    if article_slug:
        article = Article.objects.filter(slug=article_slug).first()

    inline_image = ArticleInlineImage(article=article)
    inline_image.image.save(cleaned.name, cleaned, save=True)
    return JsonResponse({
        "id": inline_image.pk,
        "url": inline_image.image.url,
        "filename": inline_image.filename,
        "markdown_path": inline_image.markdown_path,
    })


@login_required
@require_http_methods(["POST"])
def inline_image_delete_view(request, pk):
    inline_image = get_object_or_404(ArticleInlineImage, pk=pk)
    inline_image.image.delete(save=False)
    inline_image.delete()
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def preview_markdown_view(request):
    """Render markdown to HTML for live preview using the same pipeline as production.

    Returns JSON: { html: "<rendered>" }
    """
    text = request.POST.get('text', '') or ''
    html = markdown_to_html(text)
    article_slug = request.POST.get('article')
    if article_slug:
        article = Article.objects.filter(slug=article_slug).first()
        if article:
            html = bind_inline_images(html, article.inline_images.all())
    return JsonResponse({"html": str(html)})
