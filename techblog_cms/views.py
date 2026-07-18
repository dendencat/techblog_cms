import io

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db.models import Count
from django.utils.safestring import mark_safe
from PIL import Image, ImageOps, UnidentifiedImageError
from .models import Article, Category, Tag, ArticleInlineImage
from techblog_cms.templatetags.markdown_filter import markdown_to_html
from django.conf import settings
from django.http import HttpResponseNotFound

def home_view(request):
    articles = Article.objects.filter(published=True).select_related('category').order_by('-created_at')[:10]
    return render(
        request,
        'home.html',
        {
            'articles': articles,
        },
    )

def article_list_view(request):
    articles = Article.objects.filter(published=True).select_related('category').order_by('-created_at')
    paginator = Paginator(articles, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(
        request,
        'article_list.html',
        {
            'articles': page_obj,
            'page_obj': page_obj,
        },
    )

def categories_view(request):
    categories = Category.objects.annotate(num_articles=Count('article'))
    return render(
        request,
        'category_list.html',
        {
            'categories': categories,
        },
    )

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    articles = category.article_set.filter(published=True).select_related('category').order_by('-created_at')
    paginator = Paginator(articles, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
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
    return render(request, 'tag_list.html')

def tag_view(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    if request.user.is_authenticated:
        articles = tag.article_set.select_related('category').order_by('-created_at')
    else:
        articles = tag.article_set.filter(published=True).select_related('category').order_by('-created_at')

    paginator = Paginator(articles, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(
        request,
        'tag_detail.html',
        {
            'tag': tag,
            'articles': page_obj,
            'page_obj': page_obj,
        },
    )

def article_detail_view(request, slug):
    articles = Article.objects.select_related('category').prefetch_related('tags')
    # ログインしている場合は下書き記事も表示可能
    if request.user.is_authenticated:
        article = get_object_or_404(articles, slug=slug)
    else:
        article = get_object_or_404(articles, slug=slug, published=True)
    cache_key = f'article_html:{article.pk}:{article.updated_at.isoformat()}'
    content_html = cache.get(cache_key)
    if content_html is None:
        content_html = str(markdown_to_html(article.content))
        cache.set(cache_key, content_html, timeout=60 * 60 * 24)
    return render(
        request,
        'article_detail.html',
        {
            'article': article,
            'content_html': mark_safe(content_html),
        },
    )
def admin_guard(request):
    """Return 404 for all direct /admin/ access."""
    return HttpResponseNotFound('<h1>Not Found</h1>')

# Create your views here.


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


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Use Django's authenticate function but ensure consistent behavior
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            # Generic error message to prevent username enumeration
            return render(request, 'login.html', {"error": "Invalid credentials"}, status=401)
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    # GETパラメータからページ番号と表示件数を取得
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)
    
    # 表示件数を検証（5, 10, 15, 20のみ許可）
    try:
        per_page = int(per_page)
        if per_page not in [5, 10, 15, 20]:
            per_page = 5
    except (ValueError, TypeError):
        per_page = 5
    
    # 記事を取得（作成日時の降順）
    articles = Article.objects.order_by('-created_at')
    
    # ページネーション適用
    paginator = Paginator(articles, per_page)
    page_obj = paginator.get_page(page_number)
    
    # テンプレートに渡すコンテキスト
    context = {
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': [5, 10, 15, 20],
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def article_delete_view(request, slug):
    article = get_object_or_404(Article, slug=slug)
    
    if request.method == 'POST':
        article.delete()
        return redirect('article_delete_success')
    
    return render(request, 'article_delete_confirm.html', {'article': article})

@login_required
def article_delete_success_view(request):
    return render(request, 'article_delete_success.html')

@login_required
@require_http_methods(["GET", "POST"])
def article_editor_view(request, slug=None):
    article = get_object_or_404(Article, slug=slug) if slug else None
    image_help_text = (
        f"複数の画像をまとめて選択できます。Supported formats: {', '.join(settings.ARTICLE_IMAGE_ALLOWED_FORMATS)}. "
        f"Max size: {settings.ARTICLE_IMAGE_MAX_BYTES} bytes. "
        f"Max pixels: {settings.ARTICLE_IMAGE_MAX_PIXELS:,}."
    )

    def render_editor(title_value, content_value, error=None, image_error=None):
        inline_images = list(article.inline_images.order_by('uploaded_at')) if article else []
        return render(
            request,
            'article_editor.html',
            {
                "error": error,
                "image_error": image_error,
                "article": article,
                "title_value": title_value,
                "content_value": content_value,
                "image_help_text": image_help_text,
                "inline_images": inline_images,
                "media_url": settings.MEDIA_URL,
            },
        )

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        content = (request.POST.get('content') or '').strip()
        action = request.POST.get('action')  # 'save' or 'publish'
        uploaded_images = request.FILES.getlist('images')
        cleaned_images = []
        for uploaded_image in uploaded_images:
            cleaned_image, image_error = validate_article_image(uploaded_image)
            if image_error:
                display_name = getattr(uploaded_image, 'name', '選択した画像')
                return render_editor(title, content, image_error=f"{display_name}: {image_error}")
            if cleaned_image:
                cleaned_images.append(process_article_image(cleaned_image))

        if not title or not content:
            return render_editor(title, content, error="タイトルと本文は必須です。")

        published = action == 'publish'

        if article:
            article.title = title
            article.content = content
            if published:
                article.published = True
            article.save()
        else:
            category, _ = Category.objects.get_or_create(
                name='General',
                defaults={'description': 'General articles'}
            )
            article = Article(
                title=title,
                content=content,
                category=category,
                published=published,
            )
            article.save()

        for cleaned_image in cleaned_images:
            inline_image = ArticleInlineImage(article=article)
            inline_image.image.save(cleaned_image.name, cleaned_image, save=True)

        return redirect('dashboard')

    title_value = getattr(article, 'title', '')
    content_value = getattr(article, 'content', '')
    return render_editor(title_value, content_value)


@login_required
@require_http_methods(["POST"])
def preview_markdown_view(request):
    """Render markdown to HTML for live preview using the same pipeline as production.

    Returns JSON: { html: "<rendered>" }
    """
    text = request.POST.get('text', '') or ''
    html = markdown_to_html(text)
    return JsonResponse({"html": str(html)})
