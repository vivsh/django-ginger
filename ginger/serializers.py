
from django.core.paginator import Page
from django.db.models.query import QuerySet
from django.core.serializers.json import DjangoJSONEncoder

try:
    import ujson as json
except ImportError:
    import json


__all__ = ['encode', 'decode']


class JSONViewEncoder(DjangoJSONEncoder):

    def __init__(self,**kwargs):
        self.serializers = kwargs.pop('serializers', {})
        super(JSONViewEncoder, self).__init__(**kwargs)

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
        return super(JSONViewEncoder, self).default(o)


def encode(payload, **kwargs):
    return JSONViewEncoder(**kwargs).encode(payload)

def decode(payload):
    return json.loads(payload)

def process_page(page):
    items = page.object_list
    top, bottom = page.start_index(), page.end_index()
    return {
        'currentItemCount': len(items),
        'totalItems': page.paginator.count,
        'itemsPerPage': page.paginator.per_page,
        'totalPages': page.paginator.num_pages,
        'startIndex': top,
        'endIndex': bottom,
        'pageIndex': page.number
    }



