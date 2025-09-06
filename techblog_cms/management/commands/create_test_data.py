from django.core.management.base import BaseCommand
from techblog_cms.models import Category, Tag

class Command(BaseCommand):
    help = 'Creates initial test data'

    def handle(self, *args, **kwargs):
        # カテゴリーの作成
        categories = [
            ('Programming', 'プログラミング関連の記事'),
            ('Infrastructure', 'インフラストラクチャとDevOps'),
            ('Design', 'UI/UXデザインのトピックス'),
        ]
        
        for name, description in categories:
            Category.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )

        # タグの作成
        tags = ['Python', 'Django', 'Docker', 'JavaScript', 'AWS']
        for name in tags:
            Tag.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS('Successfully created test data'))
