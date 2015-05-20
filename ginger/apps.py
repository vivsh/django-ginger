
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured




class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"

    def ready(self):
        from ginger.template import prep
        prep.setup()