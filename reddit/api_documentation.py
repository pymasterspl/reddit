from typing import Any

from django.http import HttpRequest, HttpResponse
from django.views import View
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Your API Documentation",
        default_version="v1",
        description="Detailed description of your API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


class SwaggerUIView(View):
    def get(self: "SwaggerUIView", request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]) -> HttpResponse:
        return schema_view.with_ui("swagger", cache_timeout=0)(request, *args, **kwargs)


class RedocUIView(View):
    def get(self: "RedocUIView", request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]) -> HttpResponse:
        return schema_view.with_ui("redoc", cache_timeout=0)(request, *args, **kwargs)
