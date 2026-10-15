from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from . import views
from .feeds import LatestArticlesFeed, SITEMAPS
from .health import HealthCheckView, ReadinessCheckView

urlpatterns = [
    path('', views.home_view, name='home'),
    path('articles/', views.article_list_view, name='article_list'),
    re_path(r'^articles/(?P<slug>[\w\-]+)/$', views.article_detail_view, name='article_detail'),
    path('categories/', views.categories_view, name='categories'),
    path('categories/<slug:slug>/', views.category_view, name='category'),
    path('tags/', views.tags_view, name='tags'),
    path('tags/<slug:slug>/', views.tag_view, name='tag'),
    path('search/', views.search_view, name='search'),
    path('feed/', LatestArticlesFeed(), name='feed'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/articles/new/', views.article_editor_view, name='article_new'),
    re_path(r'^dashboard/articles/(?P<slug>[\w\-]+)/edit/$', views.article_editor_view, name='article_edit'),
    re_path(r'^dashboard/articles/(?P<slug>[\w\-]+)/delete/$', views.article_delete_view, name='article_delete'),
    path('dashboard/articles/delete/success/', views.article_delete_success_view, name='article_delete_success'),
    path('api/preview_markdown/', views.preview_markdown_view, name='preview_markdown'),
    path('api/images/', views.inline_image_upload_view, name='inline_image_upload'),
    path('api/images/<int:pk>/delete/', views.inline_image_delete_view, name='inline_image_delete'),
    path('admin/', views.admin_guard, name='admin_guard'),
    # Health check endpoints (for container orchestration)
    path('health/', HealthCheckView.as_view(), name='health'),
    path('ready/', ReadinessCheckView.as_view(), name='ready'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
