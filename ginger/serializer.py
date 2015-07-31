
import traceback
from django.conf import settings
from django.core.paginator import Page
from django.db.models.query import QuerySet
from django.core.serializers.json import DjangoJSONEncoder
from ginger.exceptions import NotFound, GingerHttpError, PermissionDenied, Http404

try:
    import ujson as json
except ImportError:
    import json


__all__ = ['encode', 'decode', 'JSONTemplate',
           "process_exception",
            "process_page",
            "process_redirect"]



class GingerJSONEncoder(DjangoJSONEncoder):

    def __init__(self,**kwargs):
        self.serializers = kwargs.pop('serializers', {})
        super(GingerJSONEncoder, self).__init__(**kwargs)

    def default(self, o):
        cls = o.__class__
        serializers = self.serializers
        if cls in serializers:
            return serializers[cls](o)
        if hasattr(o, 'to_json'):
            return o.to_json()
        elif isinstance(o, Page):
            return process_page(o)
        elif isinstance(o, QuerySet):
            return list(o.all())
        return super(GingerJSONEncoder, self).default(o)


class JSONTemplate(object):

    @staticmethod
    def render(context):
        return encode(context)


def encode(payload, **kwargs):
    return GingerJSONEncoder(**kwargs).encode(payload)


def decode(payload):
    return json.loads(payload)


def process_page(page):
    top, bottom = page.start_index(), page.end_index()
    return {
        'total': page.paginator.count,
        'size': len(page),
        'per_page': page.paginator.per_page,
        'total_pages': page.paginator.num_pages,
        'start_index': top,
        'end_index': bottom,
        'index': page.number
    }


def process_exception(request, exc):
    if isinstance(exc, KeyboardInterrupt):
        raise
    elif isinstance(exc, Http404):
        ex = NotFound()
        status = ex.status_code
        payload = ex.to_json()
    elif isinstance(exc, PermissionDenied):
            status = 403
            payload = {
                'type': exc.__class__.__name__,
                'message': 'Permission Denied'
            }
    elif isinstance(exc, GingerHttpError):
        status = exc.status_code
        payload = exc.to_json()
    else:
        status = 500
        payload = {
            'message': 'Internal server error',
            'type': 'ServerError'
        }
    if settings.DEBUG:
        meta = payload
        meta['type'] = exc.__class__.__name__
        meta['message'] = str(exc)
        meta['traceback'] = traceback.format_exc()
    return status, payload


def process_redirect(request, response):
    url = response.url
    return 278, {'type': 'Redirect', 'data': {'url': url}}


def encode_exception(exc):
    if isinstance(exc, KeyboardInterrupt):
        raise
    elif isinstance(exc, Http404):
        ex = NotFound()
        status = ex.status_code
        payload = ex.to_json()
    elif isinstance(exc, PermissionDenied):
            status = 403
            payload = {
                'type': exc.__class__.__name__,
                'message': 'Permission Denied'
            }
    elif isinstance(exc, GingerHttpError):
        status = exc.status_code
        payload = exc.to_json()
    else:
        status = 500
        payload = {
            'message': 'Internal server error',
            'type': 'ServerError'
        }
    payload['status_code'] = status
    if settings.DEBUG:
        meta = payload
        meta['type'] = exc.__class__.__name__
        meta['message'] = str(exc)
        meta['traceback'] = traceback.format_exc()
    return payload


def encode_object(instance):
    return {
        "data": instance
    }


def encode_collection(instance):
    if isinstance(instance, Page):
        return {
            "data": instance.object_list,
            "page": instance
        }
    else:
        return {
            "data": instance
        }


