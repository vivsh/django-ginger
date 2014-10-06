
from django.conf import settings


STAGING_ALLOWED_HOSTS = None

STAGING_SECRET = None

STAGING_SESSION_KEY = "staging-secret"

STAGING_TEMPLATE = "staging/staging.html"


def reload_settings():
    global_vars = globals()
    for key in global_vars:
        if key.startswith("STAGING_"):
            if hasattr(settings, key):
                global_vars[key] = getattr(settings, key)

reload_settings()