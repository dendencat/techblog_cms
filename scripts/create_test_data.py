import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "app"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "techblog_cms.settings")
django.setup()

from techblog_cms.models import Category, Tag, Article


def create_initial_data():
    """Create sample categories and tags."""
    Category.objects.create(
        name="Programming", description="Programming related articles"
    )
    Category.objects.create(
        name="Infrastructure", description="Infrastructure and DevOps"
    )
    Category.objects.create(name="Design", description="UI/UX Design topics")

    Tag.objects.create(name="Python")
    Tag.objects.create(name="Django")
    Tag.objects.create(name="Docker")


if __name__ == "__main__":
    create_initial_data()
    print("Successfully created test data")
