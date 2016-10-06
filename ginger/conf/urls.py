
from django.conf.urls import include, url
from ginger.views import utils


__all__ = ('include', 'url', 'scan', 'scan_to_include')


def scan(module, predicate=None):
    view_classes = utils.find_views(module, predicate=predicate)
    urls = []
    for view in view_classes:
        if hasattr(view, 'as_urls'):
            urls.extend(view.as_urls())
        else:
            urls.append(view.as_url())
    pattern = urls
    return pattern


def scan_to_include(module, predicate=None, app_name=None, namespace=None):
    return scan(module, predicate), app_name, namespace

