
import re
import json
import functools
from django.forms.forms import BoundField
from django.utils import six
from ginger import utils

__all__ = [
    "add_link_builder",
    "get_link_builder",
    "GingerNav",
    "build_links",
    "flatten_attributes",
    "create_css_class",
]

_link_builders = {}


class Link(object):

    def __init__(self, url, content, is_active=False, **kwargs):
        self.url = url
        self.content = content
        self.is_active = is_active
        for k in kwargs:
            setattr(self, k, kwargs[k])


def add_link_builder(cls, build_func):
    _link_builders[cls] = build_func


def get_link_builder(obj):
    cls = obj.__class__ if not isinstance(obj, type) else obj
    if hasattr(obj, 'build_links'):
        return obj.build_links
    else:
        try:
            func = _link_builders[cls]
        except KeyError:
            raise TypeError("No link builder associated with %r"%cls)
        else:
            return functools.partial(func, obj)


def build_links(obj, request, unique=True):
    builder = get_link_builder(obj)
    history = set()
    for link in builder(request):
        if unique and link.content in history:
            continue
        history.add(link.content)
        yield link


def bound_field_link_builder(field, request):
    url = request.get_full_path()
    form_field = field.field
    field_value = field.value
    if hasattr(form_field, 'build_links'):
        for value in form_field.build_links(request, field):
            yield value
    else:
        for code, label in form_field.choices:
            is_active = code == field_value
            link_url = utils.get_url_with_modified_params(url, {field.name: code})
            yield Link(link_url, label, is_active)


class GingerNav(object):

    def __init__(self, *links):
        self.links = []
        for link in links:
            self.add_link(**link)

    def add_link(self, url, content, **kwargs):
        link = {
            "url": url,
            "content": content
        }
        link.update(kwargs)
        self.links.append(link)

    def build_links(self, request):
        base_url = request.get_full_path()
        for link in self.links:
            url = link['url']
            content = link["content"]
            is_active = url == base_url
            yield Link(url, content, is_active)


add_link_builder(BoundField, bound_field_link_builder)


def create_css_class(*classes):
    history = set()
    frags = re.split(r'\s+', " ".join(classes).strip())
    result = []
    for value in frags:
        if value and value not in history:
            result.append(value)
            history.add(value)
    return ' '.join(result)


def flatten_attributes(attrs):
    result = []
    css = []
    for k, v in six.iteritems(attrs):
        if k == 'class':
            css.append(v)
            continue
        if isinstance(v, basestring):
            v = str(v).encode('string-escape')
        else:
            v = json.dumps(v)
        result.append("%s='%s'"% (k,v))
    css = create_css_class(*css)
    if css:
        result.append("class=%s" % css)
    return " ".join(result)

