
from django.forms.models import ModelForm
import os
import ast
import importlib
from ginger.views import meta
from ginger import utils, forms, views
from django.apps import apps
from django.utils import six


def find_empty_line(filename):
    source = open(filename).read()
    lines = source.splitlines()
    i = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line and not line.startswith("#"):
            break
    return max(i, 0)


def get_identifiers(filename):
    source = open(filename).read()
    tree = ast.parse(source)
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, ast.Assign):
            for n in child.targets:
                if isinstance(n, ast.Name):
                    yield n.id, child.lineno, child.col_offset
                else:
                    for a in ast.walk(n):
                        if isinstance(a, ast.Name):
                            yield a.id, child.lineno, child.col_offset
        if not isinstance(child, (ast.FunctionDef, ast.ClassDef)):
            continue
        name = child.name
        line = child.lineno
        col = child.col_offset
        yield name, line, col


def check_name(name, filename):
    if not os.path.exists(filename):
        return False
    for identifier, line, offset in get_identifiers(filename):
        if name == identifier:
            raise ValueError("%r is already defined in line %s of %s" % (name, line, filename))
    return False


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
    <form form_attrs(form)>
        {{# {{% csrf_token %}} #}}
        {{{{form.as_p()}}}}
        <div>
            <button type="submit"> Submit </button>
        </div>
    </form>
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

def make_dir(dir_name):
    try:
        os.makedirs(dir_name)
    except OSError:
        pass


class Code(object):

    def __init__(self, module, filename):
        self.lines = []
        self.imports = {}
        self.module = module
        self.filename = filename
        self.mark = find_empty_line(filename)

    def symbol_exists(self, name):
        try:
            return check_name(name, self.filename)
        except ValueError:
            return True

    def add(self, symbol_name, content, **kwargs):
        if self.symbol_exists(symbol_name):
            return
        context = {}
        for k, v in six.iteritems(kwargs):
            if not isinstance(v, six.string_types):
                if isinstance(v, (tuple, list)):
                    mod, name = v
                    self.add_import(mod)
                    v = "%s.%s" % (mod.__name__.rsplit(".")[-1], name)
                else:
                    self.add_import(v)
                    v = v.__name__
            context[k] = v
        content = content.format(**context).strip()
        self.lines.append("\n\n%s" % content)

    def add_import(self, symbol):
        symbol_name = symbol.__name__.rsplit(".")[-1]
        if hasattr(self.module, symbol_name) or symbol_name in self.imports:
            return
        full_name = utils.qualified_name(symbol)
        module_name, name = full_name.rsplit(".", 1)
        if name != symbol_name:
            raise ValueError("Symbol name %r should always equal %s" % (name, symbol_name))
        line = "from %s import %s\n" % (module_name, name)
        self.imports[name] = line

    def save(self):
        content = open(self.filename, "r").read().rstrip()
        lines = content.splitlines(True)
        for line in self.imports.values():
            lines.insert(self.mark, line)
        lines.append(os.linesep)
        lines.extend(self.lines)
        lines.append(os.linesep*2)
        with open(self.filename, "w") as fh:
            fh.writelines(lines)


class GingerApp(object):
    def __init__(self, app_name):
        super(GingerApp, self).__init__()
        self.app = apps.get_app_config(app_name)
        self.base_dir = self.app.path
        self.module_name = self.app.module.__name__

        self.template_base_file = self.ensure_file(self.path("templates", app_name, "base.html"),
                                                   BASE_TEMPLATE, app_name=app_name)
        self.template_dir = os.path.dirname(self.template_base_file)
        self.template_include = self.path("templates", app_name, "include")

        self.forms_file = self.ensure_file("forms.py", FORMS_MODULE)
        self.models_file = self.ensure_file("models.py", MODELS_MODULE)
        self.urls_file = self.ensure_file("urls.py", URLS_MODULE)
        self.views_file = self.ensure_file("views.py", VIEWS_MODULE)
        self.signals_file = self.ensure_file("signals.py", SIGNALS_MODULE)
        self.tasks_file = self.ensure_file("tasks.py", TASKS_MODULE)
        self.admin_file = self.ensure_file("admin.py", ADMIN_MODULE)

        make_dir(self.template_include)

        self.view_module = importlib.import_module("%s.views" % self.module_name)
        self.form_module = importlib.import_module("%s.forms" % self.module_name)
        self.model_module = importlib.import_module("%s.models" % self.module_name)


    def ensure_file(self, filename, content, **kwargs):
        context = kwargs
        filename = self.path(filename)
        make_dir(os.path.dirname(filename))
        kwargs.setdefault("app_name", self.app.label)
        if not os.path.exists(filename) or not open(filename).read().strip():
            with open(filename, "w") as fh:
                fh.write(content.format(**context))
        return filename

    def path(self, *args):
        return os.path.join(self.base_dir, *args)


class Application(GingerApp):

    def __init__(self, app_name, resource, model_name):
        super(Application, self).__init__(app_name)
        self.resource_name = self.clean_resource(resource)
        self.model_name = model_name
        self.model = self.get_model()

    def clean_resource(self, name):
        return meta.ViewInfo(self.app, name).resource_name

    def get_model(self):
        try:
            return apps.get_model(self.model_name or self.resource_name)
        except LookupError:
            if self.model_name:
                raise
            return None

    def create_view(self, info, base_class, content, **kwargs):
        name = info.view_class_name
        code = Code(self.view_module, self.views_file)
        kwargs.setdefault("app_name", self.app.label)
        code.add(name, content, name=name, base=base_class, **kwargs)
        code.save()

    def create_form(self, name, base_class, **kwargs):
        content = MODEL_FORM_CLASS if issubclass(base_class, ModelForm) else FORM_CLASS
        code = Code(self.form_module, self.forms_file)
        kwargs.setdefault("app_name", self.app.label)
        kwargs.setdefault("queryset", "")
        if self.model:
            kwargs.setdefault("model", (self.model_module, self.model.__name__))
        code.add(name, content,
                 name=name,
                 base=base_class, **kwargs)
        code.save()

    def create_template(self, info, content, **kwargs):
        kwargs["resource_name"] = info.resource_name
        filename = kwargs.pop("template_path", info.template_path)
        self.ensure_file(filename, content, **kwargs)

    def template_view(self, info):
        self.create_view(info, views.GingerTemplateView, TEMPLATE_VIEW_CLASS)
        self.create_template(info, SIMPLE_TEMPLATE)

    def delete_view(self, info):
        form_name = info.form_name
        base = forms.GingerModelForm
        self.create_form(form_name, base)
        self.create_view(info, views.GingerDeleteView, MODEL_FORM_VIEW_CLASS,
                         form_class=(self.form_module, form_name),
                         model=(self.model_module, self.model.__name__))
        self.create_template(info, FORM_TEMPLATE)

    def new_view(self, info):
        form_name = info.form_name
        base = forms.GingerForm if not self.model else forms.GingerModelForm
        self.create_form(form_name, base)
        self.create_view(info, views.GingerNewView, FORM_VIEW_CLASS,
                         form_class=(self.form_module, form_name))
        self.create_template(info, FORM_TEMPLATE)

    def edit_view(self, info):
        form_name = info.form_name
        base = forms.GingerModelForm
        self.create_form(form_name, base)
        self.create_view(info, views.GingerEditView, MODEL_FORM_VIEW_CLASS,
                         form_class=(self.form_module, form_name),
                         model=(self.model_module, self.model.__name__))
        self.create_template(info, FORM_TEMPLATE)

    def form_view(self, info):
        form_name = info.form_name
        base = forms.GingerForm if not self.model else forms.GingerModelForm
        self.create_form(form_name, base)
        self.create_view(info, views.GingerFormView, FORM_VIEW_CLASS,
                         form_class=(self.form_module, form_name))
        self.create_template(info, FORM_TEMPLATE)

    def list_view(self, info):
        base = forms.GingerForm if not self.model else forms.GingerModelForm
        form_name = info.form_name
        self.create_form(form_name, base)
        self.create_view(info, views.GingerListView, TEMPLATE_VIEW_CLASS)
        self.create_template(info, LIST_TEMPLATE)
        filename = self.path(self.template_include, "%s_item.html" % info.resource_name)
        self.create_template(info, LIST_ITEM_TEMPLATE, template_path=filename)

    def detail_view(self, info):
        self.create_view(info, views.GingerDetailView, TEMPLATE_VIEW_CLASS)
        self.create_template(info, SIMPLE_TEMPLATE)

    def search_view(self, info):
        form_name = info.form_name
        base = forms.GingerSearchForm if not self.model else forms.GingerSearchModelForm
        form_ctx = {}
        if self.model:
            form_ctx["model"] = (self.model_module, self.model.__name__)
            form_ctx["queryset"] = "queryset = models.%s.objects.all()\n" % self.model.__name__
        self.create_form(form_name, base, **form_ctx)
        self.create_view(info, views.GingerSearchView, FORM_VIEW_CLASS,
                         form_class=(self.form_module, form_name))
        self.create_template(info, LIST_TEMPLATE)
        filename = self.path(self.template_include, "%s_item.html" % info.resource_name)
        self.create_template(info, LIST_ITEM_TEMPLATE, template_path=filename)

    def generate_view(self, view_name, kind=None):
        info = meta.ViewInfo(self.app, view_name)
        if kind is None:
            kind = info.verb
        method_name = "%s_view" % kind
        try:
            func = getattr(self, method_name)
        except AttributeError:
            raise ValueError("%r is not a valid type of view" % kind)
        func(info)

    def generate_model_views(self, kinds):
        for kind in kinds:
            view_name = "%s%s" % (self.resource_name.capitalize(), kind.capitalize())
            self.generate_view(view_name, kind)
