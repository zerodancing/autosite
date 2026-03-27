import os
import sys

import django


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autoservice.settings")
django.setup()

from catalog.models import Car, CarCategory  # noqa: E402


def main():
    # В MEDIA_ROOT лежит `autosite/cars/`.
    # Относительный путь для image_url должен быть внутри MEDIA_ROOT.
    image_1 = "Porsche/Porsche 718 Boxster 982 1.webp"

    cat, _ = CarCategory.objects.get_or_create(slug="porsche-test", defaults={"name": "Тест Porsche"})
    Car.objects.update_or_create(
        brand="Porsche",
        model="718 Boxster 982",
        year=2017,
        defaults={
            "category": cat,
            "price": 0,
            "mileage_km": 0,
            "fuel_type": "",
            "transmission": "",
            "color": "",
            "description": "Тестовая машина для проверки галереи 1..5.webp",
            "image_url": image_1,
            "is_active": True,
        },
    )
    print("Seed test car done")


if __name__ == "__main__":
    main()

