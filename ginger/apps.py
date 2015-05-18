
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured




class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"

    def ready(self):
        from django.conf import settings
        from ginja import base
        from ginger.extensions import URLExtension, LoadExtension, FormExtension
        if 'django_jinja' in settings.INSTALLED_APPS:
            raise ImproperlyConfigured
        base.setup()
        base.env.finalize = lambda val: "" if val is None else val
        base.env.trim_blocks = True
        base.env.lstrip_blocks = True
        base.env.add_extension(URLExtension)
        base.env.add_extension(FormExtension)
        base.env.add_extension(LoadExtension)