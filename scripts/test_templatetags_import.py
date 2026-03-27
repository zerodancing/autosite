import os
import sys

import django


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autoservice.settings")
django.setup()


def main():
    import catalog.templatetags.car_image_filters as m

    print("import_ok=", m.__name__)
    # проверим что фильтр зарегистрирован на библиотеке
    print("has_filter_car_image_urls=", hasattr(m.register, "filters") and "car_image_urls" in m.register.filters)


if __name__ == "__main__":
    main()

