from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from catalog.models import Car, CarCategory, Service, ServiceCategory
from orders.models import Order


class OrderViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="buyer", password="testpass123")
        self.client.force_login(self.user)

        self.service_category = ServiceCategory.objects.create(name="Диагностика", slug="diagnostics")
        self.service = Service.objects.create(
            category=self.service_category,
            title="Компьютерная диагностика",
            description="Проверка ошибок и параметров",
            price_from="2500.00",
            is_active=True,
        )

        self.car_category = CarCategory.objects.create(name="Седаны", slug="sedans")
        self.car = Car.objects.create(
            category=self.car_category,
            brand="Toyota",
            model="Camry",
            year=2020,
            price="2150000.00",
            mileage_km=58000,
            is_active=True,
        )

    def test_service_order_rejects_past_datetime(self):
        past_value = timezone.localtime(timezone.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")

        response = self.client.post(
            reverse("orders:create_service_order", args=[self.service.id]),
            {"scheduled_at": past_value, "customer_comment": "Нужно посмотреть перед поездкой"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Нельзя выбрать время в прошлом.")
        self.assertEqual(Order.objects.count(), 0)

    def test_service_order_creates_valid_order(self):
        future_value = timezone.localtime(timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")

        response = self.client.post(
            reverse("orders:create_service_order", args=[self.service.id]),
            {"scheduled_at": future_value, "customer_comment": "  Проверить перед выездом  "},
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse("orders:order_detail", args=[order.id]))
        self.assertEqual(order.order_type, Order.OrderType.SERVICE)
        self.assertEqual(order.service, self.service)
        self.assertEqual(order.customer_comment, "Проверить перед выездом")
        self.assertIsNotNone(order.scheduled_at)

    def test_car_order_rejects_too_long_comment(self):
        response = self.client.post(
            reverse("orders:create_car_order", args=[self.car.id]),
            {"customer_comment": "a" * 2001},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_car_order_creates_valid_order(self):
        response = self.client.post(
            reverse("orders:create_car_order", args=[self.car.id]),
            {"customer_comment": "  Интересует история обслуживания  "},
        )

        order = Order.objects.get()

        self.assertRedirects(response, reverse("orders:order_detail", args=[order.id]))
        self.assertEqual(order.order_type, Order.OrderType.CAR)
        self.assertEqual(order.car, self.car)
        self.assertEqual(order.customer_comment, "Интересует история обслуживания")
