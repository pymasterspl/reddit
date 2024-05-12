from django.contrib import admin
from django.urls import path

from articles.views import HomeView

urlpatterns = [
        path("", HomeView.as_view(), name='home-page'),
]