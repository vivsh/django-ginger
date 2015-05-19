from django.conf import settings


JINJA2_ENVIRONMENT_OPTIONS = getattr(settings, "JINJA2_ENVIRONMENT_OPTIONS", {})

JINJA2_EXTENSIONS = getattr(settings, "JINJA2_EXTENSIONS", [])

JINJA2_AUTOESCAPE = getattr(settings, "JINJA2_AUTOESCAPE", True)

JINJA2_NEWSTYLE_GETTEXT = getattr(settings, "JINJA2_NEWSTYLE_GETTEXT", True)

JINJA2_EXCLUDED_FOLDERS = getattr(settings, "JINJA2_EXCLUDED_FOLDERS", ())


