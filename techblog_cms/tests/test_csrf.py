from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class CsrfProtectionTests(TestCase):
    """The custom login and preview endpoints must reject requests without a CSRF token."""

    def setUp(self):
        self.user = User.objects.create_user(username="editor", password="pass1234")
        self.csrf_client = Client(enforce_csrf_checks=True)

    def test_login_post_without_token_is_rejected(self):
        response = self.csrf_client.post(
            reverse("login"),
            {"username": "editor", "password": "pass1234"},
        )
        self.assertEqual(response.status_code, 403)

    def test_preview_post_without_token_is_rejected(self):
        self.csrf_client.force_login(self.user)
        response = self.csrf_client.post(reverse("preview_markdown"), {"text": "# hi"})
        self.assertEqual(response.status_code, 403)

    def test_preview_post_with_token_succeeds(self):
        self.csrf_client.force_login(self.user)
        editor_page = self.csrf_client.get(reverse("article_new"))
        self.assertEqual(editor_page.status_code, 200)
        token = self.csrf_client.cookies["csrftoken"].value

        response = self.csrf_client.post(
            reverse("preview_markdown"),
            {"text": "# hi"},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("html", response.json())
