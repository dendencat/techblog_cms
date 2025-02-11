from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView, ListView, DetailView
from .models import Article, Category, Tag  # 直接モデルをインポート

def health_check(request):
    return JsonResponse({"status": "ok"})

def index(request):
    return render(request, 'index.html')

class HomeView(TemplateView):
    template_name = "home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_title'] = 'TechBlog CMS'
        return context

class ArticleListView(ListView):
    model = Article
    template_name = "article_list.html"
    context_object_name = 'articles'
    paginate_by = 10

class ArticleDetailView(DetailView):
    model = Article
    template_name = "article_detail.html"
    context_object_name = 'article'

class CategoryListView(ListView):
    model = Category
    template_name = "category_list.html"
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = Category
    template_name = "category_detail.html"
    context_object_name = 'category'

class TagDetailView(DetailView):
    model = Tag
    template_name = "tag_detail.html"
    context_object_name = 'tag'

# Create your views here.
