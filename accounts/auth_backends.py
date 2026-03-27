from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Позволяет логиниться либо по email, либо по username.

    LoginView/AuthenticationForm всегда передаёт поле как `username`,
    поэтому мы интерпретируем значение: если в нём есть '@', то пробуем искать по email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        if username and isinstance(username, str) and "@" in username:
            user = UserModel.objects.filter(email__iexact=username).first()
            if user is None:
                return None
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            return None

        # Обычная логика ModelBackend (по username).
        return super().authenticate(request, username=username, password=password, **kwargs)

