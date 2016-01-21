
import inspect
from django.forms.formsets import BaseFormSet
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from ginger import html
from ginger.template.library import function_tag, ginger_tag
from ginger.html import layouts
from ginger.template.library import TemplateTag


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
def form_class(form):
    return html.make_class_name(form)


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


class FormTag(TemplateTag):

    def __init__(self, form, **kwargs):
        super(FormTag, self).__init__(form=form, **kwargs)

    def get_template_names(self):
        return self.context['form'].get_template_names()

