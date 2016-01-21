from django.forms.models import modelform_factory
from django.views import generic
from motifs.forms import *


class BaseView(generic.View):
    pass


class ObjectViewSet(BaseView):

    form_class = None
    filter_class = None
    serializer_class = None

    permission_classes = ()

    list_display = ()

    list_filters = ()

    list_search = ()

    exclude = None

    fields = None

    readonly_fields = None

    labels = None

    help_texts = None

    widgets = None

    form_class = None

    def get_template_names(self):
        return

    def get_labels(self):
        return self.labels

    def get_help_texts(self):
        return self.help_texts

    def get_widgets(self):
        return self.get_widgets()

    def get_exclude(self):
        return self.exclude

    def get_fields(self):
        return self.fields

    def get_readonly_fields(self):
        return self.readonly_fields

    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class
        else:
            model = self.get_queryset().model
            return modelform_factory(model=model,
                                     fields=self.get_fields(),
                                     exclude=self.get_exclude(),
                                     widgets=self.get_widgets(),

                                     )

    def get_template_context(self):
        pass

    def get_form_context(self):
        pass

    def get_form_kwargs(self):
        pass

    def get_form(self):
        pass

    def get_object(self, queryset):
        pass

    def get_queryset(self):
        pass

    def get_filtered_queryset(self):
        pass

    def add_message(self, level, ):
        pass

    def create(self, form):
        return {"object": form.create()}

    def delete(self, form):
        return form.delete()

    def update(self, form):
        return form.update()

    def get_action(self):
        return self.kwargs.get('action')

    def process_submit(self, data, files, method):
        form = self.get_form()
        if not form.is_valid():
            return
        else:
            action = self.get_action()
            if action == 'create':
                result = self.create(form)
            elif action == 'update':
                result = self.update(form)
            elif action == 'delete':
                result = self.delete(form)
    
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if not form.is_valid():
            return
        else:
            action = self.get_action()
            if action == 'create':
                result = self.create(form)
            elif action == 'update':
                result = self.update(form)
            elif action == 'delete':
                result = self.delete(form)
        return

    def get(self, request, *args, **kwargs):
        pass


class BaseViewMixin(object):

    def config(self, attr, default=None):
        value = getattr(self, attr, None)
        if value is None:
            return getattr(self.parent, attr, default)


class FormViewMixin(BaseViewMixin):

    labels = None

    help_texts = None

    widgets = None

    form_class = None

    def get_labels(self):
        return self.config("labels")

    def get_help_texts(self):
        return self.config("help_texts")

    def get_widgets(self):
        return self.config("widgets")

    def get_exclude(self):
        return self.config("widgets")

    def get_fields(self):
        return self.config("widgets")

    def get_readonly_fields(self):
        return self.config("widgets")

    def get_form_class(self):
        form_class = self.config("form_class")
        if form_class is not None:
            return form_class
        else:
            model = self.get_queryset().model
            return modelform_factory(model=model,
                                     fields=self.get_fields(),
                                     exclude=self.get_exclude(),
                                     widgets=self.get_widgets(),

                                     )

    def get_template_context(self):
        pass

    def get_form_context(self):
        pass

    def get_form_kwargs(self):
        pass

    def get_form(self):
        pass



class ListViewMixin(object):

    list_display = None

    list_filters = None

    list_search = None

    list_actions = None

    def list(self):
        return

    def update(self):
        return


class CreateObjectView(BaseView):

    def create(self):
        pass


