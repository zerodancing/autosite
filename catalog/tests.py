import tempfile
from pathlib import Path

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.forms import save_car_gallery
from catalog.models import Car, CarCategory, CarImage, SiteMetric
from catalog.templatetags.car_image_filters import car_image_urls


class CarImageUploadTests(TestCase):
    def test_filter_keeps_only_existing_gallery_files(self):
        with tempfile.TemporaryDirectory() as temp_media:
            car_dir = Path(temp_media) / "bmw"
            car_dir.mkdir(parents=True, exist_ok=True)
            (car_dir / "m5-2024-1.webp").write_bytes(b"1")
            (car_dir / "m5-2024-2.webp").write_bytes(b"2")

            with override_settings(MEDIA_ROOT=temp_media, MEDIA_URL="/cars/"):
                urls = car_image_urls("bmw/m5-2024-1.webp", 5)

            self.assertEqual(urls, ["/cars/bmw/m5-2024-1.webp", "/cars/bmw/m5-2024-2.webp"])

    def test_gallery_uploads_accumulate_in_carimage(self):
        with tempfile.TemporaryDirectory() as temp_media:
            with override_settings(MEDIA_ROOT=temp_media, MEDIA_URL="/cars/"):
                category = CarCategory.objects.create(name="Спорткары", slug="sport")
                car = Car.objects.create(
                    category=category,
                    brand="Porsche",
                    model="718 Boxster",
                    year=2024,
                    price="1000000.00",
                )

                save_car_gallery(
                    car,
                    [SimpleUploadedFile("one.webp", b"1", content_type="image/webp")],
                )
                save_car_gallery(
                    car,
                    [SimpleUploadedFile("two.webp", b"2", content_type="image/webp")],
                )

                self.assertEqual(CarImage.objects.filter(car=car).count(), 2)
                self.assertEqual(len(car.gallery_image_urls), 2)


class SiteVisitTrackingTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_anonymous_visit_is_counted_once_per_session(self):
        self.client.get(
            reverse("catalog:home"),
            HTTP_ACCEPT="text/html",
            HTTP_USER_AGENT="Mozilla/5.0",
        )
        self.client.get(
            reverse("catalog:cars_list"),
            HTTP_ACCEPT="text/html",
            HTTP_USER_AGENT="Mozilla/5.0",
        )

        metric = SiteMetric.objects.get(pk=1)
        self.assertEqual(metric.total_visits, 1)

    def test_bot_user_agent_is_not_counted(self):
        self.client.get(
            reverse("catalog:home"),
            HTTP_ACCEPT="text/html",
            HTTP_USER_AGENT="Googlebot/2.1",
        )

        self.assertFalse(SiteMetric.objects.exists())
