from django.urls import path

from articles.views import home_view

urlpatterns = [
        path("", home_view, name="home-page"),
]
