
from django.conf.urls import url, patterns, include
from ginger.conf.urls import scan
from . import views

urlpatterns = scan(views) + patterns("", url("", include("django.contrib.auth.urls")),)