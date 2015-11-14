
from django.conf import settings

ALLOWED_HOSTS = None

SECRET = "sim-sim"

SESSION_KEY = "staging-secret"

TEMPLATE = "staging/staging.html"

RESET_URL = "staging/reset/"


def get(key):
    try:
        return getattr(settings, "STAGING_" + key)
    except AttributeError:
        return globals()[key]