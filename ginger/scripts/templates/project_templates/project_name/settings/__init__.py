
from ginger.conf import env

if env.get("DJANGO_MODE", "development") == "development":
    from .development import *
else:
    from .production import *