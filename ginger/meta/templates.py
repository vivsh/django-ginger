
from os import path
from . import utils
import string


VIEWS_MODULE = """
from ginger import views as generics
"""

MODELS_MODULE = """
from django.db import models
"""

FORMS_MODULE = """
from django import forms
from ginger.forms import GingerSearchForm, GingerForm, GingerModelForm
"""


URLS_MODULE = """
from ginger.conf.urls import scan
from . import views

urlpatterns = scan(views)

"""


SIGNALS_MODULE = """
from django.dispatch import Signal
"""


TASKS_MODULE = """
from __future__ import absolute_import

from celery import shared_task
"""


ADMIN_MODULE = """
from django.contrib import admin
"""


BASE_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
    {% block ${app_name}_content %}

    {% endblock %}
{% endblock %}

"""

TEMPLATE_VIEW_CLASS = """
class ${name}(${base}):
    pass
"""

FORM_VIEW_CLASS = """
class ${name}(${base}):
    form_class = ${form_class}
"""

MODEL_FORM_VIEW_CLASS = """
class ${name}(${base}):
    form_class = ${form_class}
    queryset = ${model}.objects.all()
"""

FORM_CLASS = """
class ${name}(${base}):
    ${queryset}
    pass
"""


MODEL_FORM_CLASS = """
class ${name}(${base}):
    ${queryset}
    class Meta:
        model = ${model}
        exclude = ()
"""

BASE_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
    {% block ${app_name}_content %}

    {% endblock %}
{% endblock %}
"""

FORM_TEMPLATE = """
{% extends "${app_name}/base.html" %}
{% block ${app_name}_content %}
    {{ form_start(form) }}
        {%for field in form %}
            {{ field_tag(field) }}
        {%endfor %}
        <div>
            <button type="submit"> Submit </button>
        </div>
    {{form_end(form)}}
{% endblock %}
"""

SIMPLE_TEMPLATE = """
{% extends "${app_name}/base.html" %}
{% block ${app_name}_content %}

    <h2>Hello World</h2>

{% endblock %}
"""

LIST_TEMPLATE = """
{% extends "${app_name}/base.html" %}
{% block ${app_name}_content %}

    <ul>
    {% for object in object_list %}
        <li>
            {%include "$app_name/include/${resource_name}_item.html"%}
        </li>
    {%else %}
        <li class='empty'>
            No results found.
        </li>
    {% endfor %}
    </ul>
    <nav>
        {{ page_tag(object_list) }}
    </nav>
{% endblock %}
"""

LIST_ITEM_TEMPLATE = """
<div>
 {{object}}
</div>
"""



class Template(object):

    def __init__(self, filename, content):
        self.content = content
        self.template = string.Template(content)
        self.filename = filename

    def clean_content(self):
        indentation = None
        result = []
        for line in self.content.splitlines():
            if indentation is None:
                if not line.strip():
                    continue
                indentation = len(line) - len(line.lstrip())
            result.append(line)
        return "".join(line).strip()


    def render(self, context):
        content = self.template.safe_substitute(context)
        return utils.create_file(self.filename, content.strip())
