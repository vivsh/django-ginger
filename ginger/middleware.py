
from ginger import utils
from datetime import datetime, timedelta

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone


__all__ = ['CurrentRequestMiddleware',
           'MultipleProxyMiddleware',
           'ActiveUserMiddleware',
           'LastLoginMiddleware',
           'UsersOnlineMiddleware'
]


class CurrentRequestMiddleware(object):
    """
    This should be the first middleware
    """

    def process_request(self, request):
        ctx = utils.context()
        ctx.request = request

    def process_response(self, request, response):
        ctx = utils.context()
        ctx.request = None
        return response



class MultipleProxyMiddleware(object):
    """
    https://docs.djangoproject.com/en/dev/ref/request-response/
    """
    FORWARDED_FOR_FIELDS = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_FORWARDED_HOST',
        'HTTP_X_FORWARDED_SERVER',
    ]

    def process_request(self, request):
        """
        Rewrites the proxy headers so that only the most
        recent proxy is used.
        """
        for field in self.FORWARDED_FOR_FIELDS:
            if field in request.META:
                if ',' in request.META[field]:
                    parts = request.META[field].split(',')
                    request.META[field] = parts[-1].strip()




class LastLoginMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated():
            cache.set(str(request.user.id), True, settings.USER_ONLINE_TIMEOUT)


class ActiveUserMiddleware:

    def process_request(self, request):
        user = request.user
        if user.is_authenticated():
            now = timezone.now()
            cutoff = now - timedelta(seconds=user.ONLINE_TIMEOUT)
            accessed = user.accessed
            user.accessed = now
            if accessed < cutoff:
                user.save(update_fields=['accessed'])
#            cache.set('seen_%s' % (current_user.username), now, settings.USER_ONLINE_TIMEOUT)


class UsersOnlineMiddleware(object):

    def process_request(self, request):
        now = datetime.now()
        delta = now - timedelta(minutes=settings.USER_ONLINE_TIMEOUT)
        users_online = cache.get('users_online', {})
        guests_online = cache.get('guests_online', {})

        if request.user.is_authenticated():
            users_online[request.user.id] = now
        else:
            guest_sid = request.COOKIES.get(settings.SESSION_COOKIE_NAME, '')
            guests_online[guest_sid] = now

        for user_id in users_online.keys():
            if users_online[user_id] < delta:
                del users_online[user_id]

        for guest_id in guests_online.keys():
            if guests_online[guest_id] < delta:
                del guests_online[guest_id]

        cache.set('users_online', users_online, 60*60*24)
        cache.set('guests_online', guests_online, 60*60*24)
