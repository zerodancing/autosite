import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, OuterRef, Subquery
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import SupportConversationForm
from .models import Conversation, Message


def _user_can_access_conversation(user, conversation: Conversation) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return conversation.client_id == user.id


def _conversation_queryset(user):
    latest_message_qs = Message.objects.filter(conversation=OuterRef("pk")).order_by("-id")
    queryset = (
        Conversation.objects.select_related("client", "assigned_operator")
        .annotate(
            message_count=Count("messages"),
            last_message_text=Subquery(latest_message_qs.values("text")[:1]),
            last_message_at=Subquery(latest_message_qs.values("created_at")[:1]),
        )
        .order_by("-updated_at", "-id")
    )
    if user.is_staff:
        return queryset
    return queryset.filter(client=user)


def _sender_name(user) -> str:
    full_name = getattr(user, "full_name", "")
    full_name = full_name.strip() if isinstance(full_name, str) else ""
    return full_name or user.username


def _build_subject(subject: str, message: str) -> str:
    subject = (subject or "").strip()
    if subject:
        return subject[:200]

    compact_message = " ".join((message or "").split())
    if compact_message:
        return compact_message[:200]
    return "Новое обращение"


def _touch_conversation(conversation: Conversation, actor=None, subject: str | None = None):
    update_fields = ["updated_at"]
    conversation.updated_at = timezone.now()

    if subject and not conversation.subject:
        conversation.subject = subject[:200]
        update_fields.append("subject")

    if actor is not None and actor.is_staff and conversation.assigned_operator_id is None:
        conversation.assigned_operator = actor
        update_fields.append("assigned_operator")

    conversation.save(update_fields=update_fields)


def _serialize_message(message: Message, user):
    return {
        "id": message.id,
        "sender": _sender_name(message.sender),
        "text": message.text,
        "created_at": message.created_at.isoformat(),
        "is_me": message.sender_id == user.id,
    }


@login_required
def support_home(request):
    initial_subject = request.GET.get("subject", "").strip()
    form = None if request.user.is_staff else SupportConversationForm(initial={"subject": initial_subject})

    if request.method == "POST":
        if request.user.is_staff:
            raise Http404()

        form = SupportConversationForm(request.POST)
        if form.is_valid():
            message_text = form.cleaned_data["message"]
            conversation = Conversation.objects.create(
                client=request.user,
                subject=_build_subject(form.cleaned_data["subject"], message_text),
            )
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                text=message_text,
            )
            _touch_conversation(conversation, subject=conversation.subject)
            return redirect("support:conversation_detail", conversation_id=conversation.pk)

    conversations = list(_conversation_queryset(request.user))

    return render(
        request,
        "support/home.html",
        {
            "conversations": conversations,
            "new_conversation_form": form,
            "latest_conversation": conversations[0] if conversations else None,
            "active_conversation_id": None,
        },
    )


@login_required
def conversation_detail(request, conversation_id: int):
    conversations = list(_conversation_queryset(request.user))
    conversation = next((item for item in conversations if item.pk == conversation_id), None)
    if conversation is None or not _user_can_access_conversation(request.user, conversation):
        raise Http404()

    chat_messages = list(
        conversation.messages.select_related("sender").order_by("-id")[:100][::-1]
    )
    last_message_id = chat_messages[-1].id if chat_messages else 0

    return render(
        request,
        "support/conversation_detail.html",
        {
            "conversation": conversation,
            "conversations": conversations,
            "chat_messages": chat_messages,
            "last_message_id": last_message_id,
            "active_conversation_id": conversation.id,
            "new_conversation_form": None
            if request.user.is_staff
            else SupportConversationForm(),
        },
    )


@require_GET
@login_required
def api_get_messages(request, conversation_id: int):
    conversation = Conversation.objects.filter(pk=conversation_id).first()
    if conversation is None or not _user_can_access_conversation(request.user, conversation):
        raise Http404()

    after_id_raw = request.GET.get("after", "").strip()
    queryset = conversation.messages.select_related("sender").order_by("id")
    if after_id_raw.isdigit():
        queryset = queryset.filter(id__gt=int(after_id_raw))

    messages = list(queryset[:100])
    return JsonResponse(
        {
            "ok": True,
            "messages": [_serialize_message(message, request.user) for message in messages],
        }
    )


@require_POST
@login_required
def api_send_message(request, conversation_id: int):
    conversation = Conversation.objects.filter(pk=conversation_id).first()
    if conversation is None or not _user_can_access_conversation(request.user, conversation):
        raise Http404()

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Некорректный запрос."}, status=400)

    text = (payload.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "error": "Сообщение не должно быть пустым."}, status=400)
    if len(text) > 2000:
        return JsonResponse({"ok": False, "error": "Сообщение слишком длинное."}, status=400)

    last_message = (
        Message.objects.filter(conversation=conversation, sender=request.user).order_by("-id").first()
    )
    if last_message and timezone.now() - last_message.created_at < timedelta(milliseconds=600):
        return JsonResponse({"ok": False, "error": "Сообщения отправляются слишком часто."}, status=429)

    message = Message.objects.create(conversation=conversation, sender=request.user, text=text)
    _touch_conversation(
        conversation,
        actor=request.user,
        subject=_build_subject(conversation.subject, text),
    )

    return JsonResponse({"ok": True, "message": _serialize_message(message, request.user)})
