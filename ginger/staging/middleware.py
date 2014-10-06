
from django.conf import settings
from ginger.staging import views
from django.core.exceptions import MiddlewareNotUsed, ImproperlyConfigured
from ginger.staging import conf


class StagingMiddleware(object):
    """
    Configuration check is added here and not apps.py because it should be run if and only if
    middleware has been added
    """

    def __init__(self):
        secret = conf.STAGING_SECRET
        if not secret:
            raise ImproperlyConfigured("No STAGING_SECRET found in settings.py")
    
    def process_request(self, request):
        value = request.get_signed_cookie(conf.STAGING_SESSION_KEY, default=None)
        if value != conf.STAGING_SECRET :
            return views.stage(request)
