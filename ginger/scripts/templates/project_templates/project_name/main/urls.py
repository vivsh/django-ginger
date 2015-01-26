from django.conf.urls import url, patterns
from ginger.conf.urls import scan
from . import views

urlpatterns = scan(views)