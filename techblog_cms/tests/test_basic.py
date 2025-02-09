from django.test import TestCase
from django.urls import reverse

class BasicTests(TestCase):
    def test_home_page_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_environment_settings(self):
        """Test that critical environment settings are configured"""
        from django.conf import settings
        self.assertFalse(settings.DEBUG, 'DEBUG should be False in production')
        self.assertIn('blog.iohub.link', settings.ALLOWED_HOSTS)
