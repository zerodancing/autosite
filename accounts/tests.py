from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.forms import SignUpForm
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
        cache.clear()
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

    @override_settings(
        LIGHTWEIGHT_SECURITY_LIMITS={
            "login_failures_per_ip": 2,
            "login_failures_window_seconds": 60,
            "login_requests_per_ip": 20,
            "login_requests_window_seconds": 60,
        }
    )
    def test_login_is_temporarily_blocked_after_multiple_failures(self):
        login_url = reverse("accounts:login")

        first_response = self.client.post(
            login_url,
            {"username": self.user.username, "password": "wrong-pass"},
            REMOTE_ADDR="203.0.113.10",
        )
        second_response = self.client.post(
            login_url,
            {"username": self.user.username, "password": "wrong-pass"},
            REMOTE_ADDR="203.0.113.10",
        )
        blocked_response = self.client.post(
            login_url,
            {"username": self.user.username, "password": "wrong-pass"},
            REMOTE_ADDR="203.0.113.10",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(blocked_response.status_code, 429)
        self.assertContains(blocked_response, "Слишком много неудачных попыток входа", status_code=429)


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


class ContactNormalizationTests(TestCase):
    def test_create_user_normalizes_email_and_phone(self):
        user = CustomUser.objects.create_user(
            username="normalized",
            email="  USER@Example.COM ",
            phone="8 (999) 123-45-67",
            password="testpass123",
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.phone, "+79991234567")

    def test_signup_rejects_invalid_phone(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "fresh-user",
                "email": "Fresh@Example.com",
                "full_name": "  Ivan Ivanov  ",
                "phone": "12345",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Укажите номер телефона")
        self.assertFalse(CustomUser.objects.filter(username="fresh-user").exists())

    def test_signup_form_applies_consistent_widget_classes_to_all_profile_fields(self):
        form = SignUpForm()

        for field_name in ("full_name", "phone", "password1", "password2"):
            css_class = form.fields[field_name].widget.attrs.get("class", "")
            self.assertIn("border-slate-300/90", css_class)
            self.assertIn("focus:ring-4", css_class)
