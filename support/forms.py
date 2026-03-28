from pathlib import Path

from django import forms


IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "avif"}
VOICE_EXTENSIONS = {"mp3", "wav", "ogg", "oga", "opus", "m4a", "aac", "flac", "webm"}
MAX_IMAGE_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_VOICE_UPLOAD_BYTES = 12 * 1024 * 1024


def _extension_of(uploaded_file) -> str:
    return Path(getattr(uploaded_file, "name", "") or "").suffix.lstrip(".").lower()


def _validate_upload(
    uploaded_file,
    *,
    allowed_extensions: set[str],
    allowed_content_prefixes: tuple[str, ...],
    max_bytes: int,
    label: str,
):
    if not uploaded_file:
        return uploaded_file

    extension = _extension_of(uploaded_file)
    if extension not in allowed_extensions:
        raise forms.ValidationError(f"{label} имеет неподдерживаемый формат.")

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and not content_type.startswith(allowed_content_prefixes):
        raise forms.ValidationError(f"{label} имеет неподдерживаемый MIME-тип.")

    if getattr(uploaded_file, "size", 0) > max_bytes:
        raise forms.ValidationError(
            f"{label} слишком большой. Максимум: {max_bytes // (1024 * 1024)} МБ."
        )

    return uploaded_file


class SupportMessageBaseForm(forms.Form):
    message = forms.CharField(
        label="Сообщение",
        max_length=2000,
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "min-h-28 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400 focus:ring-0",
                "placeholder": "Опишите вопрос, проблему или пожелание. Можно отправить текст, фото, голосовое сообщение или всё вместе.",
                "rows": 5,
            }
        ),
    )
    image_upload = forms.FileField(
        label="Фото",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/*",
                "class": "block w-full text-sm text-slate-700 file:mr-3 file:rounded-xl file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:font-medium file:text-white hover:file:bg-slate-800",
            }
        ),
    )
    voice_upload = forms.FileField(
        label="Голосовое сообщение",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "audio/*,.webm,.ogg,.oga,.opus,.m4a,.aac,.wav,.mp3",
                "class": "block w-full text-sm text-slate-700 file:mr-3 file:rounded-xl file:border-0 file:bg-slate-200 file:px-4 file:py-2 file:font-medium file:text-slate-900 hover:file:bg-slate-300",
            }
        ),
    )

    empty_message_error = "Напишите сообщение, добавьте фото или прикрепите голосовое сообщение."

    def clean_message(self):
        return (self.cleaned_data.get("message") or "").strip()

    def clean_image_upload(self):
        return _validate_upload(
            self.cleaned_data.get("image_upload"),
            allowed_extensions=IMAGE_EXTENSIONS,
            allowed_content_prefixes=("image/",),
            max_bytes=MAX_IMAGE_UPLOAD_BYTES,
            label="Изображение",
        )

    def clean_voice_upload(self):
        return _validate_upload(
            self.cleaned_data.get("voice_upload"),
            allowed_extensions=VOICE_EXTENSIONS,
            allowed_content_prefixes=("audio/", "video/"),
            max_bytes=MAX_VOICE_UPLOAD_BYTES,
            label="Голосовое сообщение",
        )

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        if not cleaned_data.get("message") and not cleaned_data.get("image_upload") and not cleaned_data.get("voice_upload"):
            raise forms.ValidationError(self.empty_message_error)
        return cleaned_data


class SupportConversationForm(SupportMessageBaseForm):
    subject = forms.CharField(
        label="Тема",
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400 focus:ring-0",
                "placeholder": "Например: Хочу записаться на диагностику",
            }
        ),
    )

    def clean_subject(self):
        return (self.cleaned_data.get("subject") or "").strip()


class SupportMessageForm(SupportMessageBaseForm):
    pass
