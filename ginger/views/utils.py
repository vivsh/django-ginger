
from django.utils import six
from importlib import import_module
from ginger.views import GingerView, GingerViewSet
import inspect


__all__ = ['find_views']


def find_views(module, predicate=None):
    if isinstance(module, six.string_types):
        module = import_module(module)
    view_classes = inspect.getmembers(module, lambda a: isinstance(a, type)
                                                        and issubclass(a, (GingerView, GingerViewSet))
                                                        and not getattr(a, '__abstract__', False)
                                                        and inspect.getmodule(a) is module
                                                        and (predicate is None or predicate(a)))
    return sorted((v[1] for v in view_classes), key=lambda a: a.position)
