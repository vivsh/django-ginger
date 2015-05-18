# -*- coding: utf-8 -*-

import os

import django
import jinja2

from django.conf import settings
# from django.template import Origin
from django.template.context import BaseContext
from django.utils.importlib import import_module
from django.utils import six

from . import builtins
from . import library
from . import utils

# Default jinja extension list
DEFAULT_EXTENSIONS = [
    "jinja2.ext.do",
    "jinja2.ext.loopcontrols",
    "jinja2.ext.with_",
    "jinja2.ext.i18n",
    "jinja2.ext.autoescape",
]

JINJA2_ENVIRONMENT_OPTIONS = getattr(settings, "JINJA2_ENVIRONMENT_OPTIONS", {})
JINJA2_EXTENSIONS = getattr(settings, "JINJA2_EXTENSIONS", [])
JINJA2_AUTOESCAPE = getattr(settings, "JINJA2_AUTOESCAPE", True)
JINJA2_NEWSTYLE_GETTEXT = getattr(settings, "JINJA2_NEWSTYLE_GETTEXT", True)
JINJA2_FILTERS_REPLACE_FROM_DJANGO = getattr(settings, "JINJA2_FILTERS_REPLACE_FROM_DJANGO", True)

JINJA2_BYTECODE_CACHE_ENABLE = getattr(settings, "JINJA2_BYTECODE_CACHE_ENABLE", False)
JINJA2_BYTECODE_CACHE_NAME = getattr(settings, "JINJA2_BYTECODE_CACHE_NAME", "default")
JINJA2_BYTECODE_CACHE_BACKEND = getattr(settings, "JINJA2_BYTECODE_CACHE_BACKEND",
                                        "ginger.ginja.cache.BytecodeCache")

JINJA2_CONSTANTS = getattr(settings, "JINJA2_CONSTANTS", {})
JINJA2_TESTS = getattr(settings, "JINJA2_TESTS", {})


JINJA2_FILTERS = {
    "static": "ginger.ginja.builtins.filters.static",
    "reverseurl": "ginger.ginja.builtins.filters.reverse",
    "addslashes": "ginger.ginja.builtins.filters.addslashes",
    "capfirst": "ginger.ginja.builtins.filters.capfirst",
    "escapejs": "ginger.ginja.builtins.filters.escapejs_filter",
    # "fix_ampersands": "ginger.ginja.builtins.filters.fix_ampersands_filter",
    "floatformat": "ginger.ginja.builtins.filters.floatformat",
    "iriencode": "ginger.ginja.builtins.filters.iriencode",
    "linenumbers": "ginger.ginja.builtins.filters.linenumbers",
    "make_list": "ginger.ginja.builtins.filters.make_list",
    "slugify": "ginger.ginja.builtins.filters.slugify",
    "stringformat": "ginger.ginja.builtins.filters.stringformat",
    "truncatechars": "ginger.ginja.builtins.filters.truncatechars",
    "truncatewords": "ginger.ginja.builtins.filters.truncatewords",
    "truncatewords_html": "ginger.ginja.builtins.filters.truncatewords_html",
    "urlizetrunc": "ginger.ginja.builtins.filters.urlizetrunc",
    "ljust": "ginger.ginja.builtins.filters.ljust",
    "rjust": "ginger.ginja.builtins.filters.rjust",
    "cut": "ginger.ginja.builtins.filters.cut",
    "linebreaksbr": "ginger.ginja.builtins.filters.linebreaksbr",
    "linebreaks": "ginger.ginja.builtins.filters.linebreaks_filter",
    "removetags": "ginger.ginja.builtins.filters.removetags",
    "striptags": "ginger.ginja.builtins.filters.striptags",
    "add": "ginger.ginja.builtins.filters.add",
    "date": "ginger.ginja.builtins.filters.date",
    "time": "ginger.ginja.builtins.filters.time",
    "timesince": "ginger.ginja.builtins.filters.timesince_filter",
    "timeuntil": "ginger.ginja.builtins.filters.timeuntil_filter",
    "default_if_none": "ginger.ginja.builtins.filters.default_if_none",
    "divisibleby": "ginger.ginja.builtins.filters.divisibleby",
    "yesno": "ginger.ginja.builtins.filters.yesno",
    "pluralize": "ginger.ginja.builtins.filters.pluralize",
    "localtime": "ginger.ginja.builtins.filters.localtime",
    "utc": "ginger.ginja.builtins.filters.utc",
    "timezone": "ginger.ginja.builtins.filters.timezone",
}

if JINJA2_FILTERS_REPLACE_FROM_DJANGO:
    JINJA2_FILTERS.update({
        "title": "ginger.ginja.builtins.filters.title",
        "upper": "ginger.ginja.builtins.filters.upper",
        "lower": "ginger.ginja.builtins.filters.lower",
        "urlencode": "ginger.ginja.builtins.filters.urlencode",
        "urlize": "ginger.ginja.builtins.filters.urlize",
        "wordcount": "ginger.ginja.builtins.filters.wordcount",
        "wordwrap": "ginger.ginja.builtins.filters.wordwrap",
        "center": "ginger.ginja.builtins.filters.center",
        "join": "ginger.ginja.builtins.filters.join",
        "length": "ginger.ginja.builtins.filters.length",
        "random": "ginger.ginja.builtins.filters.random",
        "default": "ginger.ginja.builtins.filters.default",
        "filesizeformat": "ginger.ginja.builtins.filters.filesizeformat",
        "pprint": "ginger.ginja.builtins.filters.pprint",
    })

JINJA2_GLOBALS = {
    "url": "ginger.ginja.builtins.global_context.url",
    "static": "ginger.ginja.builtins.global_context.static",
    "localtime": "ginger.ginja.builtins.filters.localtime",
    "utc": "ginger.ginja.builtins.filters.utc",
    "timezone": "ginger.ginja.builtins.filters.timezone",
}


JINJA2_FILTERS.update(getattr(settings, "JINJA2_FILTERS", {}))
JINJA2_GLOBALS.update(getattr(settings, "JINJA2_GLOBALS", {}))


def dict_from_context(context):
    """
    Converts context to native python dict.
    """

    if isinstance(context, BaseContext):
        new_dict = {}
        for i in reversed(list(context)):
            new_dict.update(dict_from_context(i))
        return new_dict

    return dict(context)


class Template(jinja2.Template):
    """
    Customized jinja2 Template subclass.
    Add correct handling django context objects.
    """

    def render(self, context={}):
        new_context = dict_from_context(context)
        return super(Template, self).render(new_context)

    def stream(self, context={}):
        new_context = dict_from_context(context)
        return super(Template, self).stream(new_context)


def _iter_templatetags_modules_list():
    """
    Get list of modules that contains templatetags
    submodule.
    """
    # Django 1.7 compatibility imports
    try:
        from django.apps import apps
        all_modules = [x.name for x in apps.get_app_configs()]
    except ImportError:
        all_modules = settings.INSTALLED_APPS

    for app_path in all_modules:
        try:
            mod = import_module(app_path + ".templatetags")
            if mod is not None:
                yield (app_path, os.path.dirname(mod.__file__))
        except ImportError:
            pass


def patch_django_for_autoescape():
    """
    Patch django modules for make them compatible with
    jinja autoescape implementation.
    """
    from django.utils import safestring
    from django.forms.forms import BoundField

    try:
        from django.forms.utils import ErrorList
        from django.forms.utils import ErrorDict

    # Just for django < 1.7 compatibility
    except ImportError:
        from django.forms.util import ErrorList
        from django.forms.util import ErrorDict

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

    for app_path, mod_path in _iter_templatetags_modules_list():
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


def _initialize_builtins(env):
    """
    Inject into environment instances builtin
    filters, tests, globals, and constants.
    """
    for name, value in JINJA2_FILTERS.items():
        if isinstance(value, six.string_types):
            env.filters[name] = utils.load_class(value)
        else:
            env.filters[name] = value

    for name, value in JINJA2_TESTS.items():
        if isinstance(value, six.string_types):
            env.tests[name] = utils.load_class(value)
        else:
            env.tests[name] = value

    for name, value in JINJA2_GLOBALS.items():
        if isinstance(value, six.string_types):
            env.globals[name] = utils.load_class(value)
        else:
            env.globals[name] = value

    for name, value in JINJA2_CONSTANTS.items():
        env.globals[name] = value

    env.add_extension(builtins.extensions.CsrfExtension)
    env.add_extension(builtins.extensions.CacheExtension)


def _initialize_thirdparty(env):
    library._update_env(env)


def _initialize_i18n(env):
    # install translations
    if settings.USE_I18N:
        from django.utils import translation
        env.install_gettext_translations(translation, newstyle=JINJA2_NEWSTYLE_GETTEXT)
    else:
        env.install_null_translations(newstyle=JINJA2_NEWSTYLE_GETTEXT)


# def _initialize_template_loader(env):
#     loader = getattr(settings, "JINJA2_LOADER", None)
#
#     # Create a default loader using django template dirs
#     # and django app template dirs.
#     if loader is None:
#         from django.template.loaders import app_directories
#         default_loader_dirs = (tuple(settings.TEMPLATE_DIRS) +
#                                app_directories.app_template_dirs)
#         env.loader = jinja2.FileSystemLoader(default_loader_dirs)
#
#     # And in the last case, attach it as is.
#     else:
#         env.loader = loader


def _initialize_template_loader(env):
    from django.template.loaders import app_directories
    default_loader_dirs = (tuple(settings.TEMPLATE_DIRS) +
                           app_directories.get_app_template_dirs("templates"))
    env.loader = jinja2.FileSystemLoader(default_loader_dirs)


def _initialize_bytecode_cache(env):
    if JINJA2_BYTECODE_CACHE_ENABLE:
        cls = utils.load_class(JINJA2_BYTECODE_CACHE_BACKEND)
        env.bytecode_cache = cls(JINJA2_BYTECODE_CACHE_NAME)


def match_template(template_name, regex=None, extension=None):
    if extension is not None:
        return template_name.endswith(extension)
    elif regex:
        return regex.match(template_name)
    else:
        return False


def make_environemnt(defaults=None, clspath=None):
    """
    Create a new instance of jinja2 environment.
    """
    initial_params = {"autoescape": JINJA2_AUTOESCAPE}
    initial_params.update(JINJA2_ENVIRONMENT_OPTIONS)

    if "extensions" not in initial_params:
        initial_params["extensions"] = []

    initial_params["extensions"].extend(DEFAULT_EXTENSIONS)
    initial_params["extensions"].extend(JINJA2_EXTENSIONS)

    if settings.DEBUG:
        initial_params["undefined"] = jinja2.DebugUndefined
    else:
        initial_params["undefined"] = jinja2.Undefined

    if defaults is not None:
        initial_params.update(defaults)

    if clspath is None:
        clspath = "jinja2.Environment"

    cls = utils.load_class(clspath)
    env = cls(**initial_params)
    env.template_class = Template

    return env



def initialize(environment):
    """
    Initialize given environment populating it with
    builtins and with django i18n data.
    """
    _initialize_builtins(environment)
    _initialize_thirdparty(environment)
    _initialize_i18n(environment)
    _initialize_bytecode_cache(environment)
    _initialize_template_loader(environment)



env = None



def setup():
    global env
    env = make_environemnt()
    patch_django_for_autoescape()
    preload_templatetags_from_apps()
    initialize(env)