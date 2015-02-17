from django.utils import six
import inspect
from importlib import import_module
from django.conf.urls import patterns, include, url
from django.utils.module_loading import import_string
from ginger.views import GingerView, utils


__all__ = ('pattern', 'include', 'url', 'scan', 'scan_to_include')


def scan(module, predicate=None):
    view_classes = utils.find_views(module, predicate=predicate)
    pattern = patterns("", *[values.as_url() for values in view_classes])
    return pattern


def scan_to_include(module, predicate=None, app_name=None, namespace=None):
    return scan(module, predicate), app_name, namespace

