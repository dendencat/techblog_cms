from django.test import TestCase, Client
from django.urls import reverse

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        """Test that home page returns 200"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
