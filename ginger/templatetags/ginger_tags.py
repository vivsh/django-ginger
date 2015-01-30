
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
import re
from jinja2 import Markup
from django.template.loader import render_to_string
from django.middleware.csrf import get_token

from ginger.templates import ginger_tag, filter_tag, function_tag
from ginger import utils as gutils
from ginger import ui


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


@filter_tag
def json(values):
    return ui.as_json(values)

@ginger_tag(takes_context=True)
def ginger_field_options(context, field):
    return ui.choices_to_options(context["request"], field)

@function_tag
def field_choices(field):
    return ui.bound_field_choices(field)

def make_class_name(obj):
    return gutils.camel_to_hyphen(re.sub(r'widget|field|ginger', '',obj.__class__.__name__)).lower()

@function_tag
def field_class(field):
    return make_class_name(field.field)

@function_tag
def widget_class(field):
    return make_class_name(field.field.widget)

@function_tag
def form_class(form):
    return make_class_name(form)

@function_tag
def form_attrs(form):
    return mark_safe(get_form_attrs(form))

@function_tag
def data_attr(name, value):
    return " %s='%s' " % (name, ui.as_json(value))

@function_tag
def js_value(name, value):
    return mark_safe("<script type='text/javascript'> var %s = %s </script>" % (name, ui.as_json(value)))

