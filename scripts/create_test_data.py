from django.core.management.base import BaseCommand
from techblog_cms.models import Category, Tag, Article

def create_initial_data():
    # カテゴリーの作成
    categories = [
        Category.objects.create(name="Programming", description="Programming related articles"),
        Category.objects.create(name="Infrastructure", description="Infrastructure and DevOps"),
        Category.objects.create(name="Design", description="UI/UX Design topics")
    ]

    # タグの作成
    tags = [
        Tag.objects.create(name="Python"),
        Tag.objects.create(name="Django"),
        Tag.objects.create(name="Docker"),
    ]

class Command(BaseCommand):
    help = 'Creates initial test data'

    def handle(self, *args, **kwargs):
        create_initial_data()
        self.stdout.write(self.style.SUCCESS('Successfully created test data'))
