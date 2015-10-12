# -*- coding: utf-8 -*-

import os

from importlib import import_module
from django.utils import six
from ginger.utils import iter_app_modules


def patch_django_for_autoescape():
    """
    Patch django modules for make them compatible with
    jinja autoescape implementation.
    """
    from django.utils import safestring
    from django.forms.forms import BoundField
    from django.forms.utils import ErrorList
    from django.forms.utils import ErrorDict

    if hasattr(safestring, "SafeText"):
        if not hasattr(safestring.SafeText, "__html__"):
            safestring.SafeText.__html__ = lambda self: six.text_type(self)

    if hasattr(safestring, "SafeString"):
        if not hasattr(safestring.SafeString, "__html__"):
            safestring.SafeString.__html__ = lambda self: six.text_type(self)

    if hasattr(safestring, "SafeUnicode"):
        if not hasattr(safestring.SafeUnicode, "__html__"):
            safestring.SafeUnicode.__html__ = lambda self: six.text_type(self)

    if hasattr(safestring, "SafeBytes"):
        if not hasattr(safestring.SafeBytes, "__html__"):
            safestring.SafeBytes.__html__ = lambda self: six.text_type(self)

    if not hasattr(BoundField, "__html__"):
        BoundField.__html__ = lambda self: six.text_type(self)

    if not hasattr(ErrorList, "__html__"):
        ErrorList.__html__ = lambda self: six.text_type(self)

    if not hasattr(ErrorDict, "__html__"):
        ErrorDict.__html__ = lambda self: six.text_type(self)


def preload_templatetags_from_apps():
    """
    Iterate over all available apps in searching and preloading
    available template filters or functions for jinja2.
    """

    for _ in iter_app_modules("templatetags", deep=True):
        pass


def setup():
    patch_django_for_autoescape()
    preload_templatetags_from_apps()




