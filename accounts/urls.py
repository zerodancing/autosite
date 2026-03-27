from django.urls import path

from . import views
from .forms import LoginForm

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        views.auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            # Чтобы можно было переключать пользователя:
            # Django по умолчанию редиректит уже-аутентифицированных пользователей,
            # из-за чего “войти как admin”, когда вы уже залогинены как другой пользователь, не получается.
            redirect_authenticated_user=False,
        ),
        name="login",
    ),
    path(
        "logout/",
        # В catalog:home роут — пустой (`''`), поэтому reverse может вернуть ''.
        # Браузер при редиректе на '' иногда показывает "страница недоступна",
        # поэтому редиректим на точно существующий `/`.
        views.LogoutView.as_view(next_page="/"),
        name="logout",
    ),
    # Dev-хелпер: обновляет суперпользователя admin для входа в /admin/ без CMD.
    path("dev-admin-setup/", views.dev_admin_setup, name="dev_admin_setup"),
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="profile"),
]

