from django.urls import path

from articles.views import HomeView, PrivacyPoliceView

urlpatterns = [
        path("", HomeView.as_view(), name="home-page"),
        path("privacy-police/", PrivacyPoliceView.as_view(),
             name="privacy-policy"),

]
