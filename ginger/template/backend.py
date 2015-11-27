from __future__ import absolute_import

import os
import sys
import jinja2

from django.conf import settings
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.utils import six
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from django.template.backends.base import BaseEngine
from django.template.backends.utils import csrf_input_lazy, csrf_token_lazy
from ginger.template import settings as template_settings

from . import builtins


DEFAULT_EXTENSIONS = [
    "jinja2.ext.do",
    "jinja2.ext.loopcontrols",
    "jinja2.ext.with_",
    "jinja2.ext.i18n",
    "jinja2.ext.autoescape",
]


class Jinja2(BaseEngine):

    app_dirname = "templates"

    def __init__(self, params):
        params = params.copy()
        options = params.pop("OPTIONS", {}).copy()
        super(Jinja2, self).__init__(params)

        newstyle_gettext = options.pop("newstyle_gettext", True)

        self._context_processors = options.pop("context_processors", [])

        environment_cls = jinja2.Environment

        options.setdefault("loader", jinja2.FileSystemLoader(self.template_dirs))
        options.setdefault("extensions", DEFAULT_EXTENSIONS)
        options.setdefault("auto_reload", settings.DEBUG)
        options.setdefault("autoescape", False)

        if settings.DEBUG:
            options.setdefault("undefined", jinja2.DebugUndefined)
        else:
            options.setdefault("undefined", jinja2.Undefined)

        self.env = environment_cls(**options)

        self.env.finalize = lambda val: "" if val is None else val
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True

        self._initialize_i18n(newstyle_gettext)
        self._initialize_builtins()

    def _initialize_i18n(self, newstyle):
        # Initialize i18n support
        if settings.USE_I18N:
            from django.utils import translation
            self.env.install_gettext_translations(translation, newstyle=newstyle)
        else:
            self.env.install_null_translations(newstyle=newstyle)

    def inject_filters(self):
        from django.template.defaultfilters import register
        for name, func in six.iteritems(register.filters):
            self.env.filters[name] = func

    def inject_extensions(self):
        for ext in (
            builtins.extensions.CsrfExtension,
            builtins.extensions.CacheExtension,
            builtins.extensions.URLExtension,
            builtins.extensions.LoadExtension,
            # builtins.extensions.FormExtension
        ):
            self.env.add_extension(ext)

    def inject_globals(self):
        self.env.globals["url"] = builtins.global_context.url
        self.env.globals["static"] = builtins.global_context.static

    def _initialize_builtins(self, filters=None, tests=None, globals=None, constants=None):
        self.inject_filters()
        self.inject_globals()
        self.inject_extensions()

    @cached_property
    def context_processors(self):
        return tuple(import_string(path) for path in self._context_processors)

    def from_string(self, template_code):
        return Template(self.env.from_string(template_code), self)

    def match_template(self, template_name):
        root = template_name.strip("/").split("/",1)[0]
        _, ext = os.path.splitext(template_name)
        return ext == '.jinja' or root not in template_settings.JINJA2_EXCLUDED_FOLDERS

    def get_template(self, template_name):
        if not self.match_template(template_name):
            raise TemplateDoesNotExist("Template {} does not exists".format(template_name))
        try:
            return Template(self.env.get_template(template_name), self)
        except jinja2.TemplateNotFound as exc:
            six.reraise(TemplateDoesNotExist, TemplateDoesNotExist(exc.args),
                        sys.exc_info()[2])
        except jinja2.TemplateSyntaxError as exc:
            six.reraise(TemplateSyntaxError, TemplateSyntaxError(exc.args),
                        sys.exc_info()[2])



class Template(object):
    def __init__(self, template, backend):
        self.template = template
        self.backend = backend


    def render(self, context=None, request=None):
        if context is None:
            context = {}

        if request is not None:
            context["request"] = request
            context["csrf_input"] = csrf_input_lazy(request)
            context["csrf_token"] = csrf_token_lazy(request)

            # Support for django context processors
            for processor in self.backend.context_processors:
                context.update(processor(request))

        return self.template.render(context)
