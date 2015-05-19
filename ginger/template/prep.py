# -*- coding: utf-8 -*-

import os

from importlib import import_module
from django.utils import six


def iter_templatetags_modules_list():
    from django.apps import apps
    all_modules = [x.name for x in apps.get_app_configs()]
    for app_path in all_modules:
        try:
            mod = import_module(app_path + ".templatetags")
        except ImportError:
            pass
        else:
            if mod is not None:
                yield (app_path, os.path.dirname(mod.__file__))


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

    for app_path, mod_path in iter_templatetags_modules_list():
        if not os.path.isdir(mod_path):
            continue

        for filename in filter(lambda x: x.endswith(".py") or x.endswith(".pyc"), os.listdir(mod_path)):
            # Exclude __init__.py files
            if filename == "__init__.py" or filename == "__init__.pyc":
                continue

            file_mod_path = "%s.templatetags.%s" % (app_path, filename.rsplit(".", 1)[0])
            try:
                import_module(file_mod_path)
            except ImportError:
                pass


def setup():
    patch_django_for_autoescape()
    preload_templatetags_from_apps()




