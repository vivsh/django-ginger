
from django.apps import AppConfig


class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"

    def ready(self):
        from django.conf import settings
        from django_jinja import base
        if 'django_jinja' not in settings.INSTALLED_APPS:
            base.env.initialize()
        from ginger.extensions import URLExtension
        base.env.finalize = lambda val: "" if val is None else val
        base.env.add_extension(URLExtension)