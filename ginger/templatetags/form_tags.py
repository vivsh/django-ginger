
import inspect
from django.forms.formsets import BaseFormSet
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from ginger import html
from ginger.templates import function_tag, ginger_tag


class FormHelper(object):

    unique_key = "__ginger_form_helper"

    def __init__(self, form):
        self.form = form
        self.used = set()
        setattr(self.form, self.unique_key, self)

    @classmethod
    def get_or_create(cls, form):
        try:
            return getattr(form, cls.unique_key)
        except AttributeError:
            return cls(form)

    def get_field(self, name):
        field = self.form[name]
        self.used.add(name)
        return field

    def remaining(self):
        return [f for f in self.form if f.name not in self.used]

    def hidden_tags(self, csrf_token):
        fields = [html.wrap_csrf_token(csrf_token)]
        if not isinstance(self.form, BaseFormSet):
            for f in self.form.hidden_fields():
                if f.name not in self.used:
                    fields.append(str(f))
        return "".join(fields)

    def start_tag(self, csrf, **attrs):
        csrf = attrs.get("method", "post").lower() == "post"
        attrs = html.form_attrs(self.form, **attrs)
        form_tag = "<form {}>".format(attrs)
        hidden = self.hidden_tags(csrf)
        mgmt = force_text(getattr(self.form, "management_form", ""))
        return "%s%s%s" % (form_tag, hidden, mgmt)

    def end_tag(self):
        return "</form>"


@ginger_tag(takes_context=True, mark_safe=True)
def field_option_tags(field):
    result = []
    for choice in html.field_choices(field):
        tag = html.option(value=choice.value, selected=choice.selected)[choice.content]
        result.append(tag.render())
    return "".join(result)


@ginger_tag(takes_context=True, mark_safe=True)
def form_hidden_field_tags(context, form, csrf=True):
    request = context["request"]
    fields = []
    if csrf:
        fields.append(html.form_csrf_tag(request))
    if not isinstance(form, BaseFormSet):
        for f in form.hidden_fields():
            fields.append(str(f))
    return "".join(fields)


@function_tag
def field_range(form, *args, **kwargs):
    return html.field_range(form, *args, **kwargs)


@function_tag
def field_iter(form, *names):
    return html.iter_fields(form, names)


@ginger_tag(mark_safe=True)
def form_attrs(form, **kwargs):
    return html.form_attrs(form, **kwargs)


@ginger_tag(takes_context=True, mark_safe=True)
def form_start(context, form, **attrs):
    csrf = attrs.get("method", "post").lower() == "post"
    attrs = html.form_attrs(form, **attrs)
    form_tag = "<form {}>".format(attrs)
    hidden = form_hidden_field_tags(context, form, csrf=csrf)
    mgmt = force_text(getattr(form, "management_form", ""))
    return "%s%s%s" % (form_tag, hidden, mgmt)


@ginger_tag(mark_safe=True)
def form_end(form):
    return mark_safe("</form>")


@function_tag
def field_choices(field):
    return html.field_choices(field)


@function_tag
def field_links(request, field):
    return html.field_links(request, field)


@function_tag
def field_help(field):
    return field.help_text

@function_tag
def field_errors(field):
    return field.errors


@function_tag
def field_label(field):
    return field.label


@function_tag
def field_id(field):
    return field.id_for_label


@function_tag
def field_name(field):
    return field.html_name


@function_tag
def field_value(field):
    return field.value()


@ginger_tag(mark_safe=True)
def widget_tag(field, **attrs):
    return html.render_widget(field, *attrs)

@ginger_tag(mark_safe=True)
def field_tag(field, layout=None, **kwargs):
    return html.render_field(field, layout=layout, **kwargs)

@function_tag
def field_class(field):
    return html.field_css_class(field)


@function_tag
def widget_class(field):
    return html.widget_css_class(field)


@function_tag
def field_is(field, class_name):
    return class_is(field.field, class_name)


@function_tag
def widget_is(field, class_name):
    return class_is(field.field.widget, class_name)


@function_tag
def class_is(obj, class_name):
    class_ = obj.__class__
    return class_.__name__ == class_name or any(class_name == b.__name__ for b in inspect.getmro(class_))


@ginger_tag(takes_context=True, mark_safe=True)
def page_tag(context, page, **kwargs):
    return html.render_page(context["request"], page, **kwargs)
