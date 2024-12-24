from django.urls import include, path

from .api_documentation import RedocUIView, SwaggerUIView

urlpatterns = [
    path("core/", include("core.api_urls")),
    path("users/", include("users.api_urls")),
    path("swagger/", SwaggerUIView.as_view(), name="schema-swagger-ui"),
    path("redoc/", RedocUIView.as_view(), name="schema-redoc"),
]
