#!/usr/bin/env python
import os
import sys
import django

# Django設定を読み込む
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techblog_cms.settings')
django.setup()

from techblog_cms.models import Category, Article

# カテゴリを作成
tech_category, created = Category.objects.get_or_create(
    name='Technology',
    defaults={'description': 'Latest technology news and trends'}
)

programming_category, created = Category.objects.get_or_create(
    name='Programming',
    defaults={'description': 'Programming tutorials and tips'}
)

# 記事を作成
articles_data = [
    {
        'title': 'Introduction to Python',
        'content': 'Python is a high-level programming language known for its simplicity and readability. It is widely used for web development, data analysis, artificial intelligence, and more.',
        'category': programming_category,
        'published': True
    },
    {
        'title': 'The Future of AI',
        'content': 'Artificial Intelligence is rapidly evolving and transforming various industries. From machine learning to natural language processing, AI is becoming an integral part of our daily lives.',
        'category': tech_category,
        'published': True
    },
    {
        'title': 'Web Development Best Practices',
        'content': 'Modern web development requires following best practices to create scalable, maintainable, and user-friendly applications. This includes proper code organization, security measures, and performance optimization.',
        'category': programming_category,
        'published': True
    },
    {
        'title': 'Cloud Computing Trends',
        'content': 'Cloud computing continues to grow as businesses move their infrastructure to the cloud. Understanding the latest trends in cloud technology is essential for staying competitive.',
        'category': tech_category,
        'published': True
    }
]

for article_data in articles_data:
    article, created = Article.objects.get_or_create(
        title=article_data['title'],
        defaults={
            'content': article_data['content'],
            'category': article_data['category'],
            'published': article_data['published']
        }
    )
    if created:
        print(f"Created article: {article.title}")
    else:
        print(f"Article already exists: {article.title}")

print("Test data creation completed!")
