import json
import re
import tempfile
from datetime import timedelta

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from support.models import Conversation, Message


class SupportHomeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = CustomUser.objects.create_user(username="client1", password="testpass123")
        self.client.force_login(self.user)

    def test_support_home_renders_dashboard(self):
        response = self.client.get(reverse("support:support_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "lg:sticky lg:top-0")
        self.assertContains(response, "Поддержка")
        self.assertContains(response, "Создать обращение")

    def test_support_home_post_creates_conversation_with_first_message(self):
        response = self.client.post(
            reverse("support:support_home"),
            {
                "subject": "",
                "message": "Хочу записаться на обслуживание",
            },
        )

        conversation = Conversation.objects.get()
        first_message = Message.objects.get(conversation=conversation)

        self.assertRedirects(
            response,
            reverse("support:conversation_detail", args=[conversation.id]),
        )
        self.assertEqual(conversation.client, self.user)
        self.assertEqual(conversation.subject, "Хочу записаться на обслуживание")
        self.assertEqual(first_message.text, "Хочу записаться на обслуживание")

    def test_support_home_accepts_image_without_text(self):
        with tempfile.TemporaryDirectory() as temp_media:
            uploaded_image = SimpleUploadedFile(
                "issue-photo.png",
                b"fake-image-content",
                content_type="image/png",
            )

            with override_settings(MEDIA_ROOT=temp_media, MEDIA_URL="/cars/"):
                response = self.client.post(
                    reverse("support:support_home"),
                    {
                        "subject": "",
                        "message": "",
                        "image_upload": uploaded_image,
                    },
                )

            conversation = Conversation.objects.get()
            first_message = Message.objects.get(conversation=conversation)

        self.assertRedirects(
            response,
            reverse("support:conversation_detail", args=[conversation.id]),
        )
        self.assertEqual(conversation.subject, "Обращение с фото")
        self.assertTrue(first_message.image.name)
        self.assertEqual(first_message.preview_text, "Фото")


class SupportConversationDetailTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = CustomUser.objects.create_user(username="client1", password="testpass123")
        self.client.force_login(self.user)
        self.conversation = Conversation.objects.create(client=self.user, subject="Тестовый вопрос")
        Message.objects.create(conversation=self.conversation, sender=self.user, text="Привет")

    def test_conversation_detail_renders_for_client(self):
        response = self.client.get(
            reverse("support:conversation_detail", args=[self.conversation.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Чат поддержки")
        self.assertContains(response, "Привет")
        self.assertContains(response, "let lastId = 1;")
        self.assertContains(response, 'data-message-id="1"')
        self.assertContains(response, "const renderedMessageIds = new Set(")
        self.assertContains(response, "Записать голос")

    def test_client_cannot_open_foreign_conversation(self):
        other_user = CustomUser.objects.create_user(username="client2", password="testpass123")
        foreign_conversation = Conversation.objects.create(client=other_user, subject="Чужой диалог")

        response = self.client.get(reverse("support:conversation_detail", args=[foreign_conversation.id]))

        self.assertEqual(response.status_code, 404)


class SupportApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = CustomUser.objects.create_user(username="client1", password="testpass123")
        self.operator = CustomUser.objects.create_user(
            username="operator1",
            password="testpass123",
            is_staff=True,
        )
        self.conversation = Conversation.objects.create(client=self.user, subject="Нужна помощь")

    def test_client_send_message_updates_conversation_timestamp(self):
        old_time = timezone.now() - timedelta(days=1)
        Conversation.objects.filter(pk=self.conversation.pk).update(updated_at=old_time)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("support:api_send_message", args=[self.conversation.id]),
            data=json.dumps({"text": "Когда можно приехать?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.conversation.refresh_from_db()
        self.assertGreater(self.conversation.updated_at, old_time)
        self.assertEqual(self.conversation.messages.count(), 1)

    def test_staff_send_message_assigns_operator(self):
        self.client.force_login(self.operator)

        response = self.client.post(
            reverse("support:api_send_message", args=[self.conversation.id]),
            data=json.dumps({"text": "Здравствуйте, чем помочь?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.assigned_operator, self.operator)
        self.assertEqual(self.conversation.messages.count(), 1)

    def test_get_messages_returns_serialized_payload(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            text="Есть вопрос по оплате",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("support:api_get_messages", args=[self.conversation.id]),
            {"after": 0},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["messages"][0]["id"], message.id)
        self.assertEqual(payload["messages"][0]["text"], "Есть вопрос по оплате")

    def test_send_message_accepts_voice_attachment(self):
        self.client.force_login(self.user)

        with tempfile.TemporaryDirectory() as temp_media:
            uploaded_voice = SimpleUploadedFile(
                "voice-note.webm",
                b"fake-voice-content",
                content_type="audio/webm",
            )

            with override_settings(MEDIA_ROOT=temp_media, MEDIA_URL="/cars/"):
                response = self.client.post(
                    reverse("support:api_send_message", args=[self.conversation.id]),
                    data={"message": "", "voice_upload": uploaded_voice},
                )

            payload = response.json()
            created_message = Message.objects.get(conversation=self.conversation)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["message"]["has_voice"])
        self.assertEqual(payload["message"]["preview_text"], "Голосовое сообщение")
        self.assertTrue(created_message.voice_message.name)

    def test_send_message_accepts_mp4_voice_attachment(self):
        self.client.force_login(self.user)

        with tempfile.TemporaryDirectory() as temp_media:
            uploaded_voice = SimpleUploadedFile(
                "voice-note.mp4",
                b"fake-mp4-audio-content",
                content_type="audio/mp4",
            )

            with override_settings(MEDIA_ROOT=temp_media, MEDIA_URL="/cars/"):
                response = self.client.post(
                    reverse("support:api_send_message", args=[self.conversation.id]),
                    data={"message": "", "voice_upload": uploaded_voice},
                )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["message"]["has_voice"])
        self.assertEqual(payload["message"]["voice_mime_type"], "audio/mp4")

    @override_settings(
        LIGHTWEIGHT_SECURITY_LIMITS={
            "support_send_per_user": 1,
            "support_send_per_ip": 1,
            "support_send_window_seconds": 60,
        }
    )
    def test_send_message_is_rate_limited(self):
        second_conversation = Conversation.objects.create(client=self.user, subject="Ещё вопрос")
        self.client.force_login(self.user)

        first_response = self.client.post(
            reverse("support:api_send_message", args=[self.conversation.id]),
            data=json.dumps({"text": "Первое сообщение"}),
            content_type="application/json",
            REMOTE_ADDR="198.51.100.5",
        )
        second_response = self.client.post(
            reverse("support:api_send_message", args=[second_conversation.id]),
            data=json.dumps({"text": "Второе сообщение"}),
            content_type="application/json",
            REMOTE_ADDR="198.51.100.5",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 429)
        self.assertEqual(
            second_response.json()["error"],
            "Слишком много сообщений за короткое время. Подождите немного и попробуйте снова.",
        )


class SupportApiCsrfTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = CustomUser.objects.create_user(username="client1", password="testpass123")
        self.conversation = Conversation.objects.create(client=self.user, subject="Тест CSRF")
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)

    def test_send_message_accepts_csrf_token_from_rendered_form(self):
        detail_response = self.client.get(reverse("support:conversation_detail", args=[self.conversation.id]))
        token_match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            detail_response.content.decode("utf-8"),
        )

        self.assertIsNotNone(token_match)

        response = self.client.post(
            reverse("support:api_send_message", args=[self.conversation.id]),
            data=json.dumps({"text": "Проверка CSRF"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token_match.group(1),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.conversation.messages.count(), 1)
