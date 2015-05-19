# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse as django_reverse, NoReverseMatch
from django.contrib.staticfiles.storage import staticfiles_storage


__all__ = ['url', 'static']


def url(view_name, *args, **kwargs):
    """
    Shortcut filter for reverse url on templates. Is a alternative to
    django {% url %} tag, but more simple.

    Usage example:
        {{ url('web:timeline', userid=2) }}

    This is a equivalent to django:
        {% url 'web:timeline' userid=2 %}

    """
    return django_reverse(view_name, args=args, kwargs=kwargs)


def static(path):
    return staticfiles_storage.url(path)
