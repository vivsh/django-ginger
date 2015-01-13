
from django.views.generic import TemplateView

class AboutUsView(TemplateView):
    template_name = "main/aboutus.html"

class HelpView(TemplateView):
    template_name = "main/help.html"

class FaqView(TemplateView):
    template_name = "main/faq.html"

class PrivacyView(TemplateView):
    template_name = "main/privacy.html"

class TosView(TemplateView):
    template_name = "main/tos.html"

class HomeView(TemplateView):
    template_name = "main/home.html"
