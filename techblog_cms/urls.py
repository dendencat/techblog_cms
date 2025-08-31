from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/articles/new/', views.article_editor_view, name='article_new'),
    path('api/health/', views.health_check, name='health_check'),
    path('admin/', views.admin_guard, name='admin_guard'),
]

# Adminを隠す: 内部からのみアクセス（後でreverse proxy側で制御）
if not getattr(settings, 'HIDE_ADMIN_URL', False):
    urlpatterns.append(path('admin/', admin.site.urls))

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
