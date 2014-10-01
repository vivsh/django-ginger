
from django import forms
import inspect
from .exceptions import ValidationFailure
from django.forms.forms import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, Page


__all__ = ['ContextModelForm', 'ContextForm','SearchModelForm', 'SearchForm', 'SafeEmptyTuple']


class SafeEmptyTuple(tuple):
    def __len__(self):
        return 1


class ContextFormMixin(object):

    failure_message = None
    success_message = None

    def __init__(self, **kwargs):
        constructor = forms.Form.__init__
        kwargs.setdefault('data', {})
        keywords = set(inspect.getargspec(constructor).args)
        context = {}
        for key in kwargs.copy():
            if key in keywords or key == "instance":
                continue
            value = kwargs.pop(key)
            context[key] = value
        super(ContextFormMixin, self).__init__(**kwargs)
        self.context = self.process_context(context)

    def process_context(self, context):
        return context

    def run(self):
        if self.is_valid():
            try:
                result = self.execute(**self.context)
            except forms.ValidationError as ex:
                self.add_error(None, ex)
        if not self.is_valid():
            raise ValidationFailure(self)
        self.result = result
        return result

    def to_json(self):
        return {
            'message': self.success_message,
            'data': self.run()
        }


class ContextModelForm(ContextFormMixin, forms.ModelForm):
    pass


class ContextForm(ContextFormMixin, forms.Form):
    pass


class SearchFormMixin(ContextFormMixin):

    per_page = 20

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

    def execute(self, queryset, page=None):
        return self.apply_filters(queryset, page)

    def apply_filters(self, queryset, page=None):
        data = self.cleaned_data
        for name, value in data.items():
            if not value:
                continue
            kwargs = {}
            try:
                call = getattr(self,'handle_%s'%name)
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
            return self.paginate(queryset, page)
        return queryset

    def paginate(self, queryset, page_num):
        return Paginator(queryset, self.per_page).page(page_num)

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


class SearchModelForm(SearchFormMixin, forms.ModelForm):
    pass


class SearchForm(SearchFormMixin, forms.Form):
    pass

class DataFormMixin(object):

    def execute(self, queryset, page=None):
        result = self.apply_filter(queryset, page)
        queryset = result.object_list if self.is_paginated() else result
        columns = self.get_columns()
        items = []
        for obj in queryset:
            row = self._create_row(obj)
            items.append(row)
        result.object_list = row

    def _create_row(self, obj):
        return


    def get_field_names(self):
        return []

    def get_columns(self):
        return []