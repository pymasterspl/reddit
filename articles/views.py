from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "base.html"


class PrivacyPolicyView(TemplateView):
    template_name = "privacy-policy.html"
