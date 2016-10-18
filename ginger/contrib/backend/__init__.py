

from .sites import BackendSite

__all__ = ['site']

default_app_config = "ginger.contrib.backend.apps.BackendConfig"

site = BackendSite("backend")
