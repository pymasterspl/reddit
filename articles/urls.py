from django.urls import path

from articles.views import home_view, privacy_policy

urlpatterns = [
        path("", home_view, name="home-page"),
        path('privacy-police', privacy_policy, name='privacy-policy')
]
