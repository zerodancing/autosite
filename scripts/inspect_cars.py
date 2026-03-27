import os
import sys

import django


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autoservice.settings")
django.setup()

from catalog.models import Car  # noqa: E402
from catalog.models import CarCategory, Service, ServiceCategory  # noqa: E402


def main():
    total = Car.objects.count()
    print("cars_total=", total)
    print("car_categories_total=", CarCategory.objects.count())
    print("services_total=", Service.objects.count())
    print("service_categories_total=", ServiceCategory.objects.count())
    for c in Car.objects.all().order_by("id")[:10]:
        val = c.image_url
        if val is None:
            show = "None"
        else:
            show = repr(val)
        print(c.id, c.brand, c.model, "image_url=", show[:200])


if __name__ == "__main__":
    main()

