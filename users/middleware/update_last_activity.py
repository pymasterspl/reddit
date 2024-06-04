from django.contrib.auth import get_user_model

User = get_user_model()


class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            User.objects.get(pk=request.user.pk).update_last_activity()
        response = self.get_response(request)
        return response
