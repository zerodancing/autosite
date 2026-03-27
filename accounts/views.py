from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import activate
from django.views.decorators.http import require_GET

from .forms import SignUpForm


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("accounts:login")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    user = request.user
    return render(
        request,
        "accounts/profile.html",
        {
            "user": user,
            "full_name": getattr(user, "full_name", ""),
            "phone": getattr(user, "phone", ""),
            "role": getattr(user, "role", ""),
        },
    )


@require_GET
def set_language(request, lang):
    allowed = {code for code, _label in getattr(settings, "LANGUAGES", [])}
    if lang not in allowed:
        lang = settings.LANGUAGE_CODE

    activate(lang)

    next_url = request.GET.get("next") or reverse("catalog:home")
    if next_url and not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("catalog:home")

    response = redirect(next_url)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, max_age=365 * 24 * 60 * 60)
    return response


class LogoutView(auth_views.LogoutView):
    http_method_names = ["post", "options"]


@require_GET
def dev_admin_setup(request):
    if not settings.DEBUG:
        return HttpResponseForbidden("Dev admin setup is disabled in non-debug mode.")

    User = get_user_model()
    admin_username = "admin"
    admin_password = "admin12345"
    admin_email = "admin@example.com"

    user, _ = User.objects.get_or_create(username=admin_username, defaults={"email": admin_email})
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(admin_password)
    user.save()

    return HttpResponse(
        f"""
        <div style="font-family: sans-serif; padding: 16px;">
          <h2>Admin ready</h2>
          <p>Логин: <b>{admin_username}</b></p>
          <p>Пароль: <b>{admin_password}</b></p>
          <p><a href="/admin/">Перейти в админку</a></p>
        </div>
        """
    )
