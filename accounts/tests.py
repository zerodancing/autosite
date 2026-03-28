from django.conf import settings
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


class LoginViewTests(TestCase):
    def setUp(self):
        self.password = "testpass123"
        self.user = CustomUser.objects.create_user(
            username="tester",
            email="tester@example.com",
            password=self.password,
        )

    def test_login_accepts_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": self.password},
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.id)


class SetLanguageViewTests(TestCase):
    def test_set_language_rejects_external_redirect(self):
        response = self.client.get(
            reverse("set_language", args=["en"]),
            {"next": "https://evil.example/phishing"},
        )

        self.assertRedirects(response, reverse("catalog:home"))
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

    def test_set_language_falls_back_to_default_for_unknown_language(self):
        response = self.client.get(reverse("set_language", args=["de"]))

        self.assertRedirects(response, reverse("catalog:home"))
        self.assertEqual(
            response.cookies[settings.LANGUAGE_COOKIE_NAME].value,
            settings.LANGUAGE_CODE,
        )
