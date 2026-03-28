import hashlib

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils import translation


class AdminRussianLocaleMiddleware:
    """
    Держим админку в русском языке независимо от пользовательской cookie,
    чтобы не было смешения английских системных строк и русских кастомных полей.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            translation.activate("ru")
            request.LANGUAGE_CODE = "ru"
        return self.get_response(request)


class SiteVisitTrackingMiddleware:
    """
    Считает визиты сайта мягко: только для успешных HTML-страниц,
    не чаще одного раза за интервал на одну браузерную сессию.
    """

    session_key = "site_visit_last_tracked_at"

    def __init__(self, get_response):
        self.get_response = get_response
        self.interval_seconds = int(getattr(settings, "SITE_VISIT_INTERVAL_SECONDS", 12 * 60 * 60))

    def __call__(self, request):
        should_track_request = self._should_track_request(request)
        response = self.get_response(request)

        if should_track_request and self._should_track_response(response) and self._is_new_visit(request):
            from catalog.models import SiteMetric

            SiteMetric.increment_total_visits()
            request.session[self.session_key] = int(timezone.now().timestamp())
            request.session.modified = True

        return response

    def _should_track_request(self, request) -> bool:
        if request.method.upper() != "GET":
            return False

        path = (request.path_info or "").lower()
        if path.startswith(("/admin/", "/static/", "/media/", "/cars/", "/support/api/")):
            return False
        if path in {"/favicon.ico", "/robots.txt"}:
            return False

        accept = (request.META.get("HTTP_ACCEPT") or "").lower()
        if "text/html" not in accept and "*/*" not in accept:
            return False

        user_agent = (request.META.get("HTTP_USER_AGENT") or "").lower()
        blocked_fragments = ("bot", "spider", "crawler", "preview", "monitor", "uptime")
        return not any(fragment in user_agent for fragment in blocked_fragments)

    def _should_track_response(self, response) -> bool:
        if response.status_code != 200:
            return False
        return "text/html" in (response.headers.get("Content-Type") or "").lower()

    def _is_new_visit(self, request) -> bool:
        last_tracked_at = request.session.get(self.session_key)
        if last_tracked_at is None:
            return True

        try:
            elapsed = int(timezone.now().timestamp()) - int(last_tracked_at)
        except (TypeError, ValueError):
            return True
        return elapsed >= self.interval_seconds


class LightweightSecurityMiddleware:
    """
    Лёгкая защита от частых атак на логин и чувствительные endpoints чата.

    Ограничения намеренно мягкие: они не заменяют полноценный WAF/edge-rate-limit,
    но хорошо режут спам, брутфорс и избыточный polling без тяжёлой капчи.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.limits = getattr(settings, "LIGHTWEIGHT_SECURITY_LIMITS", {})

    def __call__(self, request):
        scope = self._match_scope(request)
        if scope:
            blocked_response = self._maybe_block_request(request, scope)
            if blocked_response is not None:
                return blocked_response

        response = self.get_response(request)

        if scope == "login":
            response = self._handle_login_response(request, response)
        return response

    def _match_scope(self, request) -> str | None:
        path = request.path_info or ""
        method = request.method.upper()

        if method == "POST" and path == "/accounts/login/":
            return "login"
        if method == "POST" and path == "/support/":
            return "support_create"
        if path.startswith("/support/api/conversations/") and path.endswith("/messages/send/") and method == "POST":
            return "support_send"
        if path.startswith("/support/api/conversations/") and path.endswith("/messages/") and method == "GET":
            return "support_poll"
        return None

    def _maybe_block_request(self, request, scope: str):
        ip = self._client_ip(request)

        if scope == "login":
            if not self._consume_limit(
                f"security:login:req:ip:{ip}",
                self.limits.get("login_requests_per_ip", 25),
                self.limits.get("login_requests_window_seconds", 300),
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много попыток входа. Попробуйте ещё раз чуть позже.",
                    self.limits.get("login_requests_window_seconds", 300),
                )

            if self._counter_value(self._login_failure_key(ip)) >= self.limits.get("login_failures_per_ip", 8):
                return self._too_many_requests(
                    request,
                    "Слишком много неудачных попыток входа. Попробуйте позже.",
                    self.limits.get("login_failures_window_seconds", 900),
                )

            identifier = self._login_identifier(request)
            if identifier and self._counter_value(self._login_failure_key(ip, identifier)) >= self.limits.get(
                "login_failures_per_ip", 8
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много неудачных попыток входа. Попробуйте позже.",
                    self.limits.get("login_failures_window_seconds", 900),
                )
            return None

        if scope == "support_create":
            if not self._consume_limit(
                f"security:support:create:ip:{ip}",
                self.limits.get("support_conversation_create_per_ip", 10),
                self.limits.get("support_conversation_create_window_seconds", 600),
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много новых обращений за короткое время. Попробуйте немного позже.",
                    self.limits.get("support_conversation_create_window_seconds", 600),
                )

            if request.user.is_authenticated and not self._consume_limit(
                f"security:support:create:user:{request.user.pk}",
                self.limits.get("support_conversation_create_per_user", 6),
                self.limits.get("support_conversation_create_window_seconds", 600),
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много новых обращений за короткое время. Попробуйте немного позже.",
                    self.limits.get("support_conversation_create_window_seconds", 600),
                )
            return None

        if scope == "support_send":
            if not self._consume_limit(
                f"security:support:send:ip:{ip}",
                self.limits.get("support_send_per_ip", 45),
                self.limits.get("support_send_window_seconds", 60),
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много сообщений за короткое время. Подождите немного и попробуйте снова.",
                    self.limits.get("support_send_window_seconds", 60),
                )

            if request.user.is_authenticated and not self._consume_limit(
                f"security:support:send:user:{request.user.pk}",
                self.limits.get("support_send_per_user", 30),
                self.limits.get("support_send_window_seconds", 60),
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много сообщений за короткое время. Подождите немного и попробуйте снова.",
                    self.limits.get("support_send_window_seconds", 60),
                )
            return None

        if scope == "support_poll":
            if not self._consume_limit(
                f"security:support:poll:ip:{ip}",
                self.limits.get("support_poll_per_ip", 360),
                self.limits.get("support_poll_window_seconds", 60),
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много запросов на обновление чата. Подождите немного.",
                    self.limits.get("support_poll_window_seconds", 60),
                )

            if request.user.is_authenticated and not self._consume_limit(
                f"security:support:poll:user:{request.user.pk}",
                self.limits.get("support_poll_per_user", 240),
                self.limits.get("support_poll_window_seconds", 60),
            ):
                return self._too_many_requests(
                    request,
                    "Слишком много запросов на обновление чата. Подождите немного.",
                    self.limits.get("support_poll_window_seconds", 60),
                )
        return None

    def _handle_login_response(self, request, response):
        ip = self._client_ip(request)
        identifier = self._login_identifier(request)

        if 300 <= response.status_code < 400:
            cache.delete(self._login_failure_key(ip))
            if identifier:
                cache.delete(self._login_failure_key(ip, identifier))
            return response

        self._bump_counter(
            self._login_failure_key(ip),
            self.limits.get("login_failures_window_seconds", 900),
        )
        if identifier:
            self._bump_counter(
                self._login_failure_key(ip, identifier),
                self.limits.get("login_failures_window_seconds", 900),
            )
        return response

    def _login_identifier(self, request) -> str:
        return (request.POST.get("username") or "").strip().lower()

    def _login_failure_key(self, ip: str, identifier: str | None = None) -> str:
        if not identifier:
            return f"security:login:fail:ip:{ip}"
        digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:16]
        return f"security:login:fail:ip:{ip}:id:{digest}"

    def _client_ip(self, request) -> str:
        forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
        if forwarded:
            return forwarded.split(",")[0].strip()
        return (request.META.get("REMOTE_ADDR") or "unknown").strip() or "unknown"

    def _counter_value(self, key: str) -> int:
        return int(cache.get(key, 0) or 0)

    def _bump_counter(self, key: str, timeout: int) -> int:
        if cache.add(key, 1, timeout=timeout):
            return 1
        try:
            return int(cache.incr(key))
        except ValueError:
            cache.set(key, 1, timeout=timeout)
            return 1

    def _consume_limit(self, key: str, limit: int, timeout: int) -> bool:
        current_value = self._bump_counter(key, timeout)
        return current_value <= limit

    def _too_many_requests(self, request, message: str, retry_after_seconds: int):
        headers = {"Retry-After": str(retry_after_seconds)}
        if request.path_info.startswith("/support/api/"):
            return JsonResponse({"ok": False, "error": message}, status=429, headers=headers)
        return HttpResponse(message, status=429, headers=headers, content_type="text/plain; charset=utf-8")
