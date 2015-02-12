
import os
from os import path
from django.apps import apps
import importlib
from . import templates


class Application(object):

    def __init__(self, app_name):
        super(Application, self).__init__()
        self.app = apps.get_app_config(app_name)
        self.base_dir = self.app.path
        self.module_name = self.app.module.__name__

        self.template_base_file = self.ensure_file(self.path("templates", app_name, "base.html"),
                                                   templates.BASE_TEMPLATE, app_name=app_name)
        self.template_dir = path.dirname(self.template_base_file)
        self.template_include = self.path("templates", app_name, "include")

        self.forms_file = self.ensure_file("forms.py", templates.FORMS_MODULE)
        self.models_file = self.ensure_file("models.py", templates.MODELS_MODULE)
        self.urls_file = self.ensure_file("urls.py", templates.URLS_MODULE)
        self.views_file = self.ensure_file("views.py", templates.VIEWS_MODULE)
        self.signals_file = self.ensure_file("signals.py", templates.SIGNALS_MODULE)
        self.tasks_file = self.ensure_file("tasks.py", templates.TASKS_MODULE)
        self.admin_file = self.ensure_file("admin.py", templates.ADMIN_MODULE)

        self.make_dir(self.template_include)

        self.view_module = importlib.import_module("%s.views" % self.module_name)
        self.form_module = importlib.import_module("%s.forms" % self.module_name)
        self.model_module = importlib.import_module("%s.models" % self.module_name)

    def make_dir(dir_name):
        try:
            os.makedirs(dir_name)
        except OSError:
            pass

    def ensure_file(self, filename, content, **kwargs):
        context = kwargs
        filename = self.path(filename)
        self.make_dir(path.dirname(filename))
        kwargs.setdefault("app_name", self.app.label)
        if not path.exists(filename) or not open(filename).read().strip():
            with open(filename, "w") as fh:
                fh.write(content.format(**context))
        return filename

    def path(self, *args):
        return path.join(self.base_dir, *args)
