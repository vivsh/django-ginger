
from django.apps import AppConfig


class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"

    def ready(self):
        from django.conf import settings
        from django_jinja import base
        if 'django_jinja' not in settings.INSTALLED_APPS:
            base.setup_django_lte_17()
        from ginger.extensions import URLExtension, LoadExtension, FormExtension
        base.env.finalize = lambda val: "" if val is None else val
        base.env.trim_blocks = True
        base.env.lstrip_blocks = True
        base.env.add_extension(URLExtension)
        base.env.add_extension(FormExtension)
        base.env.add_extension(LoadExtension)