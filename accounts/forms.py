from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


COMMON_INPUT_ATTRS = {
    "class": "mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none focus:border-slate-400",
}


class SignUpForm(UserCreationForm):
    full_name = forms.CharField(label=_("Имя и фамилия"), max_length=200, required=False)
    phone = forms.CharField(label=_("Телефон"), max_length=30, required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "full_name", "phone", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={**COMMON_INPUT_ATTRS, "autocomplete": "username", "placeholder": "Логин"}),
            "email": forms.EmailInput(attrs={**COMMON_INPUT_ATTRS, "autocomplete": "email", "placeholder": "Email"}),
            "full_name": forms.TextInput(attrs=COMMON_INPUT_ATTRS | {"autocomplete": "name", "placeholder": "Имя и фамилия"}),
            "phone": forms.TextInput(attrs=COMMON_INPUT_ATTRS | {"autocomplete": "tel", "placeholder": "Телефон"}),
            "password1": forms.PasswordInput(attrs={**COMMON_INPUT_ATTRS, "autocomplete": "new-password", "placeholder": "Пароль"}),
            "password2": forms.PasswordInput(attrs={**COMMON_INPUT_ATTRS, "autocomplete": "new-password", "placeholder": "Повторите пароль"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data.get("full_name", "")
        user.phone = self.cleaned_data.get("phone", "")
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Вьюха `LoginView` всегда шлёт значение в поле `username`.
    Мы позволяем пользователю вводить email (см. auth backend),
    поэтому placeholder = "email или логин".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                **COMMON_INPUT_ATTRS,
                "placeholder": "email или логин",
                "autocomplete": "username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                **COMMON_INPUT_ATTRS,
                "autocomplete": "current-password",
                "placeholder": "Пароль",
            }
        )

