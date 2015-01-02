from django.utils import six
import inspect
from django.utils.module_loading import import_string
from django.conf.urls import patterns, include, url
from ginger.views import GingerView


__all__ = ('pattern', 'include', 'url', 'scan')


def scan(module, predicate=None):
    if isinstance(module, six.string_types):
        module = import_string(module)
    view_classes = inspect.getmembers(module, lambda a: isinstance(a, type)
                                                        and issubclass(a, GingerView)
                                                        and inspect.getmodule(a) is module
                                                        and (predicate is None or predicate(a)))
    pattern = patterns("", *[values[1].as_url() for values in view_classes])
    return pattern

