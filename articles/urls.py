from django.urls import path

from articles.views import HomeView, PrivacyPolicyView

urlpatterns = [
    path("", HomeView.as_view(), name="home-page"),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy-policy"),
]
