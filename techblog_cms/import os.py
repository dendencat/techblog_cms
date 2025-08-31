import os
from django.test import TestCase
from django.core.wsgi import get_wsgi_application

# techblog_cms/test_wsgi.py

class WsgiTests(TestCase):
    def test_wsgi_application_creation(self):
        # WSGIアプリケーションが正しくインスタンス化されるかテスト
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techblog_cms.settings')
        application = get_wsgi_application()
        self.assertIsNotNone(application)
        # アプリケーションが呼び出し可能か確認
        self.assertTrue(callable(application))