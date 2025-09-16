from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .models import Article, Category, Tag
from techblog_cms.templatetags.markdown_filter import markdown_to_html
from django.conf import settings
from django.http import HttpResponseNotFound

def health_check(request):
    return JsonResponse({"status": "ok"})

def index(request):
    return render(request, 'index.html')

def home_view(request):
    articles = Article.objects.filter(published=True).order_by('-created_at')[:10]
    categories = Category.objects.all()
    tags = Tag.objects.all()
    return render(
        request,
        'home.html',
        {
            'articles': articles,
            'categories': categories,
            'tags': tags,
        },
    )

def article_list_view(request):
    articles = Article.objects.filter(published=True).order_by('-created_at')
    categories = Category.objects.all()
    tags = Tag.objects.all()
    return render(
        request,
        'article_list.html',
        {
            'articles': articles,
            'categories': categories,
            'tags': tags,
        },
    )

def categories_view(request):
    categories = Category.objects.all()
    tags = Tag.objects.all()
    return render(
        request,
        'category_list.html',
        {
            'categories': categories,
            'tags': tags,
        },
    )

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    articles = category.article_set.filter(published=True).order_by('-created_at')
    categories = Category.objects.all()
    tags = Tag.objects.all()
    return render(
        request,
        'category_detail.html',
        {
            'category': category,
            'articles': articles,
            'categories': categories,
            'tags': tags,
        },
    )

def tags_view(request):
    tags = Tag.objects.all()
    categories = Category.objects.all()
    return render(
        request,
        'tag_list.html',
        {
            'tags': tags,
            'categories': categories,
        },
    )

def tag_view(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    if request.user.is_authenticated:
        articles = tag.article_set.order_by('-created_at')
    else:
        articles = tag.article_set.filter(published=True).order_by('-created_at')

    categories = Category.objects.all()
    tags = Tag.objects.all()
    return render(
        request,
        'tag_detail.html',
        {
            'tag': tag,
            'articles': articles,
            'categories': categories,
            'tags': tags,
        },
    )

def article_detail_view(request, slug):
    # ログインしている場合は下書き記事も表示可能
    if request.user.is_authenticated:
        article = get_object_or_404(Article, slug=slug)
    else:
        article = get_object_or_404(Article, slug=slug, published=True)
    categories = Category.objects.all()
    tags = Tag.objects.all()
    return render(
        request,
        'article_detail.html',
        {
            'article': article,
            'categories': categories,
            'tags': tags,
        },
    )
def admin_guard(request):
    """Direct /admin/ access guard. Show 404 if HIDE_ADMIN_URL is True."""
    if getattr(settings, 'HIDE_ADMIN_URL', False):
        return HttpResponseNotFound('<h1>Not Found</h1>')
    return redirect('/admin/')

# Create your views here.


@require_http_methods(["GET", "POST"])
@csrf_exempt
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

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        content = (request.POST.get('content') or '').strip()
        action = request.POST.get('action')  # 'save' or 'publish'

        if not title or not content:
            context = {
                "error": "タイトルと本文は必須です。",
                "article": article,
                "title_value": title,
                "content_value": content,
            }
            return render(request, 'article_editor.html', context)

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

        return redirect('dashboard')

    context = {
        'article': article,
        'title_value': getattr(article, 'title', ''),
        'content_value': getattr(article, 'content', ''),
    }
    return render(request, 'article_editor.html', context)


@login_required
@require_http_methods(["POST"]) 
@csrf_exempt
def preview_markdown_view(request):
    """Render markdown to HTML for live preview using the same pipeline as production.

    Notes:
    - CSRF exempt to simplify AJAX preview while authenticated.
    - Returns JSON: { html: "<rendered>" }
    """
    text = request.POST.get('text', '') or ''
    html = markdown_to_html(text)
    return JsonResponse({"html": str(html)})
