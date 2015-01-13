from django.conf.urls import url, patterns
from . import views

urlpatterns = patterns('',
    url(r'^about_us/$', views.AboutUsView.as_view(), name="about_us"),
    url(r'^privacy/$', views.PrivacyView.as_view(), name="privacy"),
    url(r'^tos/$', views.TosView.as_view(), name="tos"),
    url(r'^faq/$', views.FaqView.as_view(), name="faq"),
    url(r'^help/$', views.HelpView.as_view(), name="help"),
    url(r'^$', views.HomeView.as_view(), name="home"),
)