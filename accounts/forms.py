from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser
from .normalization import normalize_email, normalize_phone


COMMON_INPUT_ATTRS = {
    "class": "mt-1 w-full rounded-[1rem] border border-slate-300/90 bg-white/90 px-4 py-3 text-slate-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.55)] outline-none transition focus:border-slate-900 focus:bg-white focus:ring-4 focus:ring-slate-900/10",
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
            "phone": forms.TextInput(
                attrs=COMMON_INPUT_ATTRS
                | {
                    "autocomplete": "tel",
                    "inputmode": "tel",
                    "placeholder": "+7 999 123-45-67",
                }
            ),
            "password1": forms.PasswordInput(attrs={**COMMON_INPUT_ATTRS, "autocomplete": "new-password", "placeholder": "Пароль"}),
            "password2": forms.PasswordInput(attrs={**COMMON_INPUT_ATTRS, "autocomplete": "new-password", "placeholder": "Повторите пароль"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].widget.attrs.update(
            {
                **COMMON_INPUT_ATTRS,
                "autocomplete": "name",
                "placeholder": "Имя и фамилия",
            }
        )
        self.fields["phone"].widget.attrs.update(
            {
                **COMMON_INPUT_ATTRS,
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+7 999 123-45-67",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                **COMMON_INPUT_ATTRS,
                "autocomplete": "new-password",
                "placeholder": "Пароль",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                **COMMON_INPUT_ATTRS,
                "autocomplete": "new-password",
                "placeholder": "Подтверждение пароля",
            }
        )

    def clean_email(self):
        return normalize_email(self.cleaned_data.get("email"))

    def clean_phone(self):
        return normalize_phone(self.cleaned_data.get("phone"), raise_on_error=True)

    def clean_full_name(self):
        return (self.cleaned_data.get("full_name") or "").strip()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data.get("full_name", "")
        user.phone = self.cleaned_data.get("phone", "")
        user.email = self.cleaned_data.get("email", "")
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

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if "@" in username:
            return normalize_email(username)
        return username
