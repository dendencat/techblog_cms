import os
import subprocess
import sys
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

REPO_ROOT = Path(__file__).resolve().parents[2]


class LogoutMethodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='writer', password='s3cure-pass-123')
        self.client.force_login(self.user)

    def test_logout_via_get_is_rejected(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        # Still logged in
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)

    def test_logout_via_post_logs_out(self):
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)


class ProductionSecretKeyTests(TestCase):
    """settings.py must refuse to start a non-debug process with a weak SECRET_KEY."""

    def _load_settings(self, secret_key):
        env = {
            k: v for k, v in os.environ.items()
            if k not in {'TESTING', 'PYTEST_CURRENT_TEST', 'PYTEST_ADDOPTS'}
        }
        env.update({'DEBUG': 'False', 'SECRET_KEY': secret_key, 'DJANGO_SETTINGS_MODULE': 'techblog_cms.settings'})
        return subprocess.run(
            [sys.executable, '-c', 'import techblog_cms.settings'],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60,
        )

    def test_placeholder_and_short_keys_are_rejected(self):
        for key in ('', 'django-insecure-default-key', 'your-secret-key-here', 'short-key'):
            with self.subTest(key=key):
                result = self._load_settings(key)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('ImproperlyConfigured', result.stderr)

    def test_strong_key_is_accepted(self):
        result = self._load_settings('k' * 20 + 'Xy9_-abcdefghijklmnopqrstuvwxyz0123456789')
        self.assertEqual(result.returncode, 0, result.stderr)
