from django import forms


class SupportConversationForm(forms.Form):
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
    message = forms.CharField(
        label="Сообщение",
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "class": "min-h-28 w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400 focus:ring-0",
                "placeholder": "Опишите вопрос, проблему или пожелание. Оператор увидит сообщение сразу.",
                "rows": 5,
            }
        ),
    )

    def clean_subject(self):
        return (self.cleaned_data.get("subject") or "").strip()

    def clean_message(self):
        message = (self.cleaned_data.get("message") or "").strip()
        if not message:
            raise forms.ValidationError("Напишите сообщение для поддержки.")
        return message
