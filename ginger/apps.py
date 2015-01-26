
from django.apps import AppConfig


class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"

    def ready(self):
        from django.conf import settings
        from django_jinja import base
        if 'django_jinja' not in settings.INSTALLED_APPS:
            env = base.env
            if hasattr(env, "initialize"):
                base.env.initialize()
            else:
                base.setup_django_lte_17()
        from ginger.extensions import URLExtension
        base.env.finalize = lambda val: "" if val is None else val
        base.env.add_extension(URLExtension)