
from django.apps import AppConfig


class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"

    def ready(self):
        from django.conf import settings
        if 'django_jinja' not in settings.INSTALLED_APPS:
            from django_jinja import base
            base.env.add_extension('ginger.extensions.URLExtension')
            base.env.initialize()