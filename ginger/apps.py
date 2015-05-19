
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured




class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"

    def ready(self):
        from django.conf import settings
        from ginger.template import prep
        prep.setup()
        # env = engine.env
        # from ginger.extensions import URLExtension, LoadExtension, FormExtension
        # env.finalize = lambda val: "" if val is None else val
        # env.trim_blocks = True
        # env.lstrip_blocks = True
        # env.add_extension(URLExtension)
        # env.add_extension(FormExtension)
        # env.add_extension(LoadExtension)
        # from ginger.templatetags import allauth_tags
        # from ginger.templatetags import form_tags
        # from ginger.templatetags import ginger_tags