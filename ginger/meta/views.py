
from django.utils.module_loading import import_string
from ginger import views as generics
from django.utils import six
from . import templates
from .app import Application


class ViewPatch(object):

    def __init__(self, view_class):
        if isinstance(view_class, six.string_types):
            view_class = import_string(view_class)
        self.view_class = view_class
        self.meta = view_class.meta
        self.app = Application(self.meta.app.app_label)

    def kind(self):
        return "template"
        kinds = {
            generics.GingerTemplateView: "template",
            generics.GingerFormView: "form",
            generics.GingerNewView: "new",
            generics.GingerDetailView: "detail",
            generics.GingerEditView: "edit",
            generics.GingerDeleteView: "edit",
            generics.GingerSearchView: "search"
        }

    def get_model(self):
        view = self.get_view_class()
        return view.model

    def patch(self):
        kind = self.kind()
        if kind == "template":
            self.patch_template_view()
        if kind == "form":
            pass

    def patch_form_view(self):
        pass

    def patch_template_view(self):
        context = {
            "app_name": self.app.label
        }
        templates.Template(self.meta.template_path, templates.SIMPLE_TEMPLATE).render(context)


    def __str__(self):
        return str(dict(
            app_label=self.app.label,
            template_dir=self.template_dir,
            template_name=self.template_name,
            template_path=self.template_path,
            resource_name=self.resource_name,
            form_name=self.form_name,
            form_path=self.form_path,
            verb=self.verb
        ))
