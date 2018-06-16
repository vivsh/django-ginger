
from collections import namedtuple
from django.utils.encoding import force_text
from django.template import loader
from django.utils.safestring import mark_safe
from jinja2 import Markup
import re
import json
import functools
from django.forms.forms import BoundField
from django.utils import six
from ginger import utils, serializer, nav


__all__ = [
    "add_link_builder",
    "get_link_builder",
    "build_links",
    "flatten_attributes",
    "create_css_class",
    "Link",
    "UIComponent",
    "as_json"
]

_link_builders = {}


Link = nav.Link


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


def is_selected_choice(values, choice):
    if not isinstance(values, (list, tuple)):
        values = (values, )
    text_choice = force_text(choice)
    for v in values:
        if v == choice or text_choice == force_text(v):
            return True
    return False


Choice = namedtuple("Choice", ["name", "value", "content", "selected"])

def bound_field_choices(field):
    form_field = field.field
    field_value = field.value()
    name = field.html_name
    for code, label in form_field.choices:
        is_active = is_selected_choice(field_value, code)
        yield Choice(name, code, label, is_active)

def bound_field_link_builder(field, request):
    url = request.get_full_path()
    form_field = field.field
    field_value = field.value()
    if hasattr(form_field, 'build_links'):
        for value in form_field.build_links(request, field):
            yield value
    else:
        for code, label in form_field.choices:
            is_active = is_selected_choice(field_value, code)
            link_url = utils.get_url_with_modified_params(url, {field.name: code})
            yield Link(content=label, url=link_url, is_active=is_active, value=code)


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


# noinspection PyPackageRequirements
def choices_to_options(request, bound_field):
    tags = []
    for link in build_links(bound_field, request):
        selected = "selected" if link.is_active else ""
        html = "<option value='%s' %s> %s </option>" % (link.value, selected, link.content)
        tags.append(html)
    return Markup("".join(tags))



def as_json(values):
    content = serializer.encode(values)
    return Markup(content)


class UIComponent(object):

    template_name = None

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        return kwargs

    def render(self, context, **kwargs):
        ctx = {}
        template_names = self.get_template_names()
        ctx.update(context)
        ctx.update(kwargs)
        return mark_safe(loader.render_to_string(template_names, context=ctx))

