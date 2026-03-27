from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("", views.support_home, name="support_home"),
    path("conversation/<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),

    # API для чата (polling)
    path(
        "api/conversations/<int:conversation_id>/messages/",
        views.api_get_messages,
        name="api_get_messages",
    ),
    path(
        "api/conversations/<int:conversation_id>/messages/send/",
        views.api_send_message,
        name="api_send_message",
    ),
]

