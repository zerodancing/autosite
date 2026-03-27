from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("my/", views.my_orders, name="my_orders"),
    path("create/service/<int:service_id>/", views.create_service_order, name="create_service_order"),
    path("create/car/<int:car_id>/", views.create_car_order, name="create_car_order"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
]

