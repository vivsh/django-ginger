# -*- coding: utf-8 -*-

import functools
import itertools
from django.utils.module_loading import import_string
import jinja2
import os

from django.template.response import TemplateResponse
from django.conf import settings
from django.http import HttpResponse
from django.template import TemplateDoesNotExist
from django.template.loaders import app_directories
from django.template.loaders import filesystem
from ginger.template import library

from ginger.serializer import JSONTemplate


__all__ = [
    # "FileSystemLoader",
    # "AppLoader",
    # "Template",
    "GingerResponse",
    "ginger_tag",
    "filter_tag",
    "function_tag",
    "test_tag",
    "select_template",
    "get_template",
    "render_to_string",
    "render_to_response",
    "get_or_select_template",
]


JINJA2_TEMPLATE_EXTENSION = getattr(settings, 'JINJA2_TEMPLATE_EXTENSION', '.jinja')

JINJA2_EXCLUDE_FOLDERS = set(getattr(settings,'JINJA2_EXCLUDE_FOLDERS',()))


def get_env():
    from django.template import engine
    return engine.env


def from_string(value):
    return get_env().from_string(value)

def get_template(template_name):
    return get_env().get_template(template_name)


def select_template(template_names):
    return get_env().select_template(template_names)


def get_or_select_template(templates):
    return get_env().get_or_select_template(templates)


def render_to_string(template_names, context):
    return get_env().get_or_select_template(template_names).render(context)


def render_to_response(template_names, context, response_class=HttpResponse, response_kwargs=None):
    defaults = {
        "status": 200,
        "content_type": "text/html"
    }
    if response_kwargs is not None:
        defaults.update(response_kwargs)
    content = render_to_string(template_names, context)
    return response_class(content, **defaults)


def ginger_tag(template=None, name=None, takes_context=False, mark_safe=False):
    def closure(orig_func):
        func = orig_func
        name_ = name or getattr(func,'_decorated_function',func).__name__
        if template:
            def wrapper(*args, **kwargs):
                t = get_env().get_template(template)
                values = orig_func(*args,**kwargs)
                result = t.render( values )
                result = jinja2.Markup(result)
                return result
            func = functools.update_wrapper(wrapper, func)
        elif mark_safe:
            def wrapper(*args, **kwargs):
                result = orig_func(*args, **kwargs)
                return jinja2.Markup(result)
            func = functools.update_wrapper(wrapper, func)
        if takes_context:
            func = jinja2.contextfunction(func)
        library.global_function(name_, func)
        return orig_func
    return closure


function_tag = library.global_function

filter_tag = library.filter

test_tag = library.test


def field_layout(func):
    from ginger.html import forms
    name = func.__name__
    forms.register_layout(name, func)
    return func


class GingerResponse(TemplateResponse):

    def is_json(self):
        return self["content-type"] == "application/json"

    def resolve_context(self, context):
        if self.is_json():
            return context
        else:
            context = super(GingerResponse, self).resolve_context(context)
            return context

    def resolve_template(self, template):
        return JSONTemplate if self.is_json() else super(GingerResponse, self).resolve_template(template)



