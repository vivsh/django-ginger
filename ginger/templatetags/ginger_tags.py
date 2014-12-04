
from django.utils.encoding import force_text
import re
from jinja2 import Markup, escape

from django.forms.forms import BoundField
from django.template.loader import render_to_string
from django.middleware.csrf import get_token

from ginger.templates import ginger_tag, filter_tag
from ginger import utils as gutils
from ginger import ui, serializer


@ginger_tag(mark_safe=True)
def ginger_form_attributes(form, **kwargs):
    return get_form_attrs(form, **kwargs)


@ginger_tag(mark_safe=True)
def ginger_form_slice(first=None,last=None,form=None,**kwargs):
    if hasattr(first, 'fields'):
        form = first
        first = None
    else:
        form = getattr(first,'form', getattr(last,'form',form)) 
    keys = form.fields.keys()
    first = keys.index(first.name) if first else None
    last = keys.index(last.name) + 1 if last else None
    return ginger_fields(*list(form[field] for field in keys[first:last]), **kwargs)

        
@ginger_tag(mark_safe=True)        
def ginger_fields(*fields,**kwargs):
    content = map(lambda f : ginger_field(f, **kwargs), fields)
    return "".join(content)

            
@ginger_tag(mark_safe=True)            
def ginger_field(field, **kwargs):
    return field_to_html(field, kwargs)


@ginger_tag(mark_safe=True)
def ginger_widget(field,**kwargs):
    wid = field.field.widget
    wid.attrs.update(kwargs)
    return unicode(field)


@ginger_tag(takes_context=True, mark_safe=True)
def ginger_csrf_tag(context):
    return create_csrf_tag(context)


@ginger_tag(takes_context=True)
def ginger_links(context, obj, **kwargs):
    return ui.build_links(obj, context["request"], **kwargs)

@ginger_tag(takes_context=True)
def with_request(context, func, **kwargs):
    kwargs['request'] = context["request"]
    return func(**kwargs)

@ginger_tag(takes_context=True)
def current_url(context, **kwargs):
    request = context['request']
    return gutils.get_url_with_modified_params(request, kwargs)


def get_form_attrs(form, **kwargs):
    attrs = kwargs.copy()
    attrs.setdefault("method", "post")
    attrs['enctype']='multipart/form-data' if form.is_multipart() else 'application/x-www-form-urlencoded'
    return ui.flatten_attributes(attrs)


def create_csrf_tag(context):
    request = context["request"]
    csrf_token = context.get('csrf_token', get_token(request))
    if not csrf_token: raise Exception("No csrf token provided in the context")
    return "<div style='display:none'><input type='hidden' name='csrfmiddlewaretoken' value='%s' /></div>" % (
        force_text(csrf_token),)


def field_to_html(field, kwargs):
    if field.is_hidden:
        return str(field)
    layout = kwargs.pop("template", None) or "default"
    process = lambda a: gutils.camel_to_hyphen(re.sub( r'widget|field', '',a.__class__.__name__)).lower()
    field_class_name = process(field.field)
    widget = field.field.widget
    widget_class_name = process(widget)
    template_name = "fields/%s.html"%field_class_name.replace("-", "_")
    field_name = field.name
    is_valid = not field.errors
    context = {
        'is_valid': is_valid,
        'field_errors': format_errors(field.errors),
        'field': field,
        'field_name': field_name,
        'field_class': field_class_name,
        'widget': widget,
        'widget_class': widget_class_name
    }
    template = [template_name, "ginger/fields/%s.html"%layout]
    html = render_to_string(template, context)
    return html


def format_errors(error_list, **kwargs):
    if not error_list:
        return Markup("<ul class='errorlist'></ul>")
    return Markup(error_list)


class RenderField(object):

    def __init__(self, request, field):
        self.field = field
        self.request = request

    def widget(self):
        return self.widget

    def help(self):
        return self.field.field.help_text

    def error_tag(self):
        return self.field.errors()

    def label(self):
        return self.field

    def label_tag(self):
        return

    def help_tag(self):
        return

    def value(self):
        pass

    def data(self):
        pass

    def choices(self):
        pass

    def links(self):
        pass

    def options(self):
        pass


class FormRenderer(object):

    def __init__(self, form):
        self.form = form
        self.fields = []
        self.form.__renderer = self
        self.reload()

    def reload(self):
        self.fields = list(self.form.fields.keys())

    @classmethod
    def get_or_create(self, form):
        try:
            self.form.__renderer
        except AttributeError:
            return FormRenderer(form)

    def coerce(self, key):
        if isinstance(key, BoundField):
            return key.name, key
        else:
            return key, self.form[key]

    def field(self, key):
        name, field = self.coerce(key)
        self.fields.remove(name)
        return field

    def get_field_context(self, field):
        pass

    def render_field(self):
        pass

    def __iter__(self):
        for key in self.fields:
            name, field = self.coerce(key)
            yield field

    def slice(self, first, last=None, step=None):
        return



@filter_tag
def json(values):
    content = serializer.encode(values)
    return Markup(content)