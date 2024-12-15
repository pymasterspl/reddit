from django.template import Context
from rest_framework.generics import CreateAPIView

from .models import User
from .serializers import UserSerializer


class UserApiRegistration(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_context(self: "UserApiRegistration") -> Context:
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
