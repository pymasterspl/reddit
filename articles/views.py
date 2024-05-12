from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "base.html"


class PrivacyPoliceView(TemplateView):
    template_name = "privacy-police.html"
