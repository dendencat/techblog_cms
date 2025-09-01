from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('articles/', views.article_list_view, name='article_list'),
    path('articles/<slug:slug>/', views.article_detail_view, name='article_detail'),
    path('categories/', views.categories_view, name='categories'),
    path('categories/<slug:slug>/', views.category_view, name='category'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/articles/new/', views.article_editor_view, name='article_new'),
    path('dashboard/articles/<slug:slug>/delete/', views.article_delete_view, name='article_delete'),
    path('dashboard/articles/delete/success/', views.article_delete_success_view, name='article_delete_success'),
    path('api/health/', views.health_check, name='health_check'),
    path('admin/', views.admin_guard, name='admin_guard'),
]

# Adminを隠す: 内部からのみアクセス（後でreverse proxy側で制御）
if not getattr(settings, 'HIDE_ADMIN_URL', False):
    urlpatterns.append(path('admin/', admin.site.urls))

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
