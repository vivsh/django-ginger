

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
{{% extends "base.html" %}}
{{% block content %}}
    {{% block {app_name}_content %}}

    {{% endblock %}}
{{% endblock %}}

"""

TEMPLATE_VIEW_CLASS = """
class {name}({base}):
    pass
"""

FORM_VIEW_CLASS = """
class {name}({base}):
    form_class = {form_class}
"""

MODEL_FORM_VIEW_CLASS = """
class {name}({base}):
    form_class = {form_class}
    queryset = {model}.objects.all()
"""

FORM_CLASS = """
class {name}({base}):
    {queryset}
    pass
"""


MODEL_FORM_CLASS = """
class {name}({base}):
    {queryset}
    class Meta:
        model = {model}
        exclude = ()
"""

BASE_TEMPLATE = """
{{% extends "base.html" %}}
{{% block content %}}
    {{% block {app_name}_content %}}

    {{% endblock %}}
{{% endblock %}}
"""

FORM_TEMPLATE = """
{{% extends "{app_name}/base.html" %}}
{{% block {app_name}_content %}}
    {{{{ form_start(form) }}}}
        {{{{form.as_p()}}}}
        <div>
            <button type="submit"> Submit </button>
        </div>
    {{{{form_end()}}}}
{{% endblock %}}
"""

SIMPLE_TEMPLATE = """
{{% extends "{app_name}/base.html" %}}
{{% block {app_name}_content %}}

    <h2>Hello World</h2>

{{% endblock %}}
"""

LIST_TEMPLATE = """
{{% extends "{app_name}/base.html" %}}
{{% block {app_name}_content %}}

    <ul>
    {{% for object in object_list %}}
        <li>
            {{%include "{app_name}/include/{resource_name}_item.html"%}}
        </li>
    {{%else %}}
        <li class='empty'>
            No results found.
        </li>
    {{% endfor %}}

{{% endblock %}}
"""

LIST_ITEM_TEMPLATE = """
<div>
{{{{object}}}}
</div>
"""
