
from django.apps.config import AppConfig


class BackendConfig(AppConfig):
    name = "ginger.contrib.backend"
    verbose_name = "Backend"
    settings_key = "STAGING"

    def ready(self):
        from ginger.contrib.backend import site
        site.discover()
