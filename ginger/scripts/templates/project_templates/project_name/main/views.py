
import ginger.views as generic
from django.views.generic import TemplateView


class AboutUsView(generic.GingerTemplateView):
    url_regex = "about_us/"


class HelpView(generic.GingerTemplateView):
    url_regex = "main/"


class FaqView(generic.GingerTemplateView):
    url_regex = "faq/"


class PrivacyView(generic.GingerTemplateView):
    url_regex = "privacy/"


class TosView(generic.GingerTemplateView):
    url_regex = "tos/"


class HomeView(generic.GingerTemplateView):
    url_regex = ""
