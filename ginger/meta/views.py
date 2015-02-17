import contextlib
import inspect
from os import path
from django.contrib.auth.models import User
from django.utils.module_loading import import_string
from django.utils import six
from ginger import forms
from ginger import views as generics
from ginger import patch, utils
from django.apps import apps
from . import templates
from .app import Application


class ViewPatch(object):

    def __init__(self, view_class):
        if isinstance(view_class, six.string_types):
            view_class = import_string(view_class)
        self.view_class = view_class
        self.meta = view_class.meta
        self.app = Application(self.meta.app.label)
        self.module = inspect.getmodule(self.view_class)
        self.model = self.get_model()

    def get_kind(self):
        kinds = (
            (generics.GingerTemplateView, "template"),
            (generics.GingerFormView, "form"),
            (generics.GingerNewView, "new"),
            (generics.GingerDetailView, "detail"),
            (generics.GingerEditView, "edit"),
            (generics.GingerDeleteView, "delete"),
            (generics.GingerSearchView, "search")
        )
        if issubclass(self.view_class, generics.GingerSearchView):
            return "search"
        if issubclass(self.view_class, generics.GingerFormView):
            return "form"
        if issubclass(self.view_class, generics.GingerTemplateView):
            return "template"
        return "template"

    @contextlib.contextmanager
    def class_patch(self):
        module = patch.Module(self.module)
        class_ = module.Class(self.view_class)
        yield class_
        module.save()

    def get_model(self):
        view = self.view_class
        model = getattr(view, "model", None)
        if model:
            return model
        parts = self.meta.resource_name.split("_")
        while parts:
            class_name = "".join(p.capitalize() for p in parts)
            model = next((m for m in apps.get_models() if m.__name__ == class_name), None)
            if model:
                return model
            parts.pop(0)
        return None

    def patch(self):
        kind = self.get_kind()
        method = "patch_%s_view" % kind
        return getattr(self, method)()

    def create_template(self, content, context=None, filename=None):
        if context is None:
            context = {}
        defaults = {
            "app_name": self.app.label,
            "resource_name": self.meta.resource_name
        }
        defaults.update(context)
        if filename is None:
            filename = self.meta.template_path

        templates.Template(filename, content).render(defaults)

    def patch_form_view(self):
        model = self.model
        base = forms.GingerForm if not model else forms.GingerModelForm
        module = patch.Module(self.app.form_module)
        cls = module.Class(self.meta.form_name, [base])
        form_class = cls
        if model:
            meta_cls = form_class.Class("Meta")
            meta_cls.Attr("model", model)
            meta_cls.Attr("exclude", ())

            func = form_class.Def("get_queryset", [])
            func("""
            return {model}.objects.all()
            """, model=model)
        module.save()

        with self.class_patch() as cls:
            cls.Attr("form_class", form_class)
            if model:
                cls.Attr("model", model)
        self.create_template(templates.FORM_TEMPLATE)

    def patch_search_view(self):
        model = self.model
        base = forms.GingerSearchForm if not model else forms.GingerSearchModelForm
        module = patch.Module(self.app.form_module)
        cls = module.Class(self.meta.form_name, [base])
        form_class = cls
        if model:
            meta_cls = form_class.Class("Meta")
            meta_cls.Attr("model", model)
            meta_cls.Attr("exclude", ())

            func = form_class.Def("get_queryset", [], varkw="kwargs")
            func("""
            return {model}.objects.all()
            """, model=model)
        module.save()

        with self.class_patch() as cls:
            cls.Attr("form_class", form_class)
            if model:
                cls.Attr("model", model)
        self.create_template(templates.LIST_TEMPLATE)
        self.create_template(templates.LIST_ITEM_TEMPLATE,
                             filename=path.join(self.meta.template_dir,
                                            "%s/include/%s_item.html" % (self.app.label,
                                                                         self.meta.resource_name)))

    def patch_template_view(self):
        with self.class_patch() as cls:
            cls.Def("get_thing")
            cls.Attr("name", "hello")
        self.create_template(templates.SIMPLE_TEMPLATE)

    def __str__(self):
        return str(dict(
            app_label=self.app.label,
            template_dir=self.meta.template_dir,
            template_name=self.meta.template_name,
            template_path=self.meta.template_path,
            resource_name=self.meta.resource_name,
            form_name=self.meta.form_name,
            form_path=self.meta.form_path,
            verb=self.meta.verb
        ))
