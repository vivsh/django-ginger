
from django.apps.config import AppConfig


class StagingConfig(AppConfig):
    name = "ginger.contrib.staging"
    verbose_name = "Staging"
    settings_module = "ginger.contrib.staging.settings"
    settings_key = "STAGING"

