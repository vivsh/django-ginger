import os
from ginger import utils


class ViewInfo(object):

    def __init__(self, app, view_name):
        super(ViewInfo, self).__init__()
        self.app = app
        self.view_name = view_name
        self.url_name = utils.camel_to_underscore(self.view_name).replace("_view", "").strip("_")

    @property
    def template_dir(self):
        folder = self.app.path
        return os.path.join(folder, "templates")

    @property
    def template_name(self):
        name = "%s/%s.html" % (self.app.label, self.url_name)
        return name

    @property
    def template_path(self):
        return os.path.join(self.template_dir, self.template_name)

    @property
    def form_name(self):
        parts = self.url_name.split("_")
        parts.append("Form")
        return "".join(p.capitalize() for p in parts)

    @property
    def view_module_name(self):
        return "%s.views" % (self.app.module.__name__, )

    @property
    def form_module_name(self):
        return "%s.forms" % (self.app.module.__name__, )

    @property
    def view_class_name(self):
        return "%sView" % "".join(p.capitalize() for p in self.url_name.split("_"))

    @property
    def resource_name(self):
        return "_".join(self.url_name.split("_")[:-1])

    @property
    def form_path(self):
        return os.path.join(self.app.path, "forms.py")

    @property
    def verb(self):
        return self.url_name.split("_")[-1]

    @property
    def url_verb(self):
        verb = self.verb
        return verb if verb not in {"home", "index", "list", "detail", "default"} else ""




