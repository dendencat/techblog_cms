from django.apps import AppConfig


class TechblogCmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'techblog_cms'

    def ready(self):
        from . import signals  # noqa: F401
