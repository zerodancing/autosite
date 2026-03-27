from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="tester", password="testpass123")
        self.client.force_login(self.user)

    def test_logout_requires_post(self):
        response = self.client.get(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_post_logs_user_out(self):
        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, "/")
        self.assertNotIn("_auth_user_id", self.client.session)
