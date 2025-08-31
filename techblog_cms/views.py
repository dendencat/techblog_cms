from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Article
from django.conf import settings
from django.http import HttpResponseNotFound

def health_check(request):
    return JsonResponse({"status": "ok"})

def index(request):
    return render(request, 'index.html')
def admin_guard(request):
    """Direct /admin/ access guard. Show 404 if HIDE_ADMIN_URL is True."""
    if getattr(settings, 'HIDE_ADMIN_URL', False):
        return HttpResponseNotFound('<h1>Not Found</h1>')
    return redirect('/admin/')

# Create your views here.


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {"error": "ユーザー名またはパスワードが違います。"}, status=401)
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    recent_articles = Article.objects.order_by('-created_at')[:5]
    return render(request, 'dashboard.html', {"recent_articles": recent_articles})


@login_required
@require_http_methods(["GET", "POST"])
def article_editor_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        if not title or not content:
            return render(request, 'article_editor.html', {"error": "タイトルと本文は必須です。"})
        # 簡易作成（カテゴリ/タグは省略）
        article = Article.objects.create(title=title, content=content, slug=title.lower().replace(' ', '-'))
        return redirect('dashboard')
    return render(request, 'article_editor.html')
