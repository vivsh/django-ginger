
from django import forms
import inspect
from django.core.paginator import Page

from ginger.exceptions import ValidationFailure
from ginger import utils, paginator


__all__ = ['GingerModelForm', 
           'GingerForm',
           'GingerSearchModelForm',
           'GingerSearchForm',
           'GingerSafeEmptyTuple',
           'GingerFormMixin',
           'GingerSearchFormMixin']


class GingerSafeEmptyTuple(tuple):
    def __len__(self):
        return 1


class GingerFormMixin(object):

    failure_message = None
    success_message = None
    ignore_errors = False

    def __init__(self, **kwargs):
        parent_cls = forms.Form if not isinstance(self, forms.ModelForm) else forms.ModelForm
        constructor = parent_cls.__init__
        keywords = set(inspect.getargspec(constructor).args)
        if "ignore_errors" in kwargs:
            self.ignore_errors = kwargs.pop("ignore_errors")
        context = {}
        for key in kwargs.copy():
            if key in keywords:
                continue
            value = kwargs.pop(key)
            context[key] = value
        super(GingerFormMixin, self).__init__(**kwargs)
        self.context = self.process_context(context)

    @property
    def result(self):
        return self.__result

    def process_context(self, context):
        return context

    def get_success_message(self):
        return self.success_message

    def get_failure_message(self):
        return self.failure_message

    @classmethod
    def class_oid(cls):
        """
        Obfuscated class id
        :return: str
        """
        return utils.create_hash(utils.qualified_name(cls))

    def is_submitted(self, data):
        return self.submit_name() in data

    @classmethod
    def submit_name(cls):
        return "submit-%s" % cls.uid()

    def run(self):
        if not self.is_valid():
            raise ValidationFailure(self)
        return self.result

    def is_valid(self):
        func = super(GingerFormMixin, self).is_valid
        try:
            return self.result
        except AttributeError:
            pass
        result = None
        if func() or self.ignore_errors:
            try:
                result = self.execute(**self.context)
            except forms.ValidationError as ex:
                self.add_error(None, ex)
            finally:
                self.__result = result
        return func()

    def execute(self, **kwargs):
        return {}

    def to_json(self):
        return {
            'message': self.get_success_message(),
            'data': self.run()
        }


class GingerModelForm(GingerFormMixin, forms.ModelForm):
    pass


class GingerForm(GingerFormMixin, forms.Form):
    pass


class GingerSearchFormMixin(GingerFormMixin):

    per_page = 20
    page_limit = 10
    parameter_name = "page"
    ignore_errors = True

    def insert_null(self, field_name, label, initial=None):
        field = self.fields[field_name]
        if initial is None:
            initial = field.empty_value
        field.required = False
        field.initial = initial
        choices = list(field.choices)
        if choices[0][0] == field.empty_value or not choices[0][0]:
            choices = choices[1:]
        choices.insert(0, (field.empty_value or "", label))
        field.choices = tuple(choices)

    def get_queryset(self, **kwargs):
        return self.queryset

    def execute(self, **kwargs):
        return self.apply_filters(**kwargs)

    def apply_filters(self, page=None, base_url=None, parameter_name="page",
                      page_limit=10, per_page=20, **kwargs):
        queryset = self.get_queryset(**kwargs)
        data = self.cleaned_data
        for name, value in data.items():
            if not value:
                continue
            kwargs = {}
            try:
                call = getattr(self, 'handle_%s'%name)
            except AttributeError:
                if isinstance(value, (tuple,list)):
                    name = '%s__in'%name
                kwargs[name] = value
                result = queryset.filter(**kwargs)
            else:
                result = call(queryset, value, data)
            if result is not None:
                queryset = result
        if page is not None:
            return self.paginate(queryset, page,
                                 parameter_name=parameter_name,
                                 page_limit=page_limit, per_page=per_page)
        return queryset

    @staticmethod
    def paginate(object_list, page, **kwargs):
        return paginator.paginate(object_list, page, **kwargs)

    def is_paginated(self):
        return 'page' in self.context

    def to_json(self):
        result = self.run()
        if isinstance(result, Page):
            return {
                'data': result.object_list,
                'page': result
            }
        else:
            return {
                'data': result
            }


class GingerSearchModelForm(GingerSearchFormMixin, forms.ModelForm):
    pass


class GingerSearchForm(GingerSearchFormMixin, forms.Form):
    pass
