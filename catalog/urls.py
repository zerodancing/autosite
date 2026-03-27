from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),

    path("services/", views.services_list, name="services_list"),
    path("services/<int:service_id>/", views.service_detail, name="service_detail"),

    path("cars/", views.cars_list, name="cars_list"),
    path("cars/<int:car_id>/", views.car_detail, name="car_detail"),
]

