from collections.abc import Callable

from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse

User = get_user_model()


class UpdateLastActivityMiddleware:
    def __init__(self: "UpdateLastActivityMiddleware", get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self: "UpdateLastActivityMiddleware", request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            User.objects.get(pk=request.user.pk).update_last_activity()
        return self.get_response(request)
