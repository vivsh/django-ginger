
import datetime
import inspect
from django.core.exceptions import ImproperlyConfigured
from django.http.request import QueryDict
from django.utils import six
from django import forms
from django.core.paginator import Page

from ginger.exceptions import ValidationFailure
from ginger import utils, paginator


__all__ = ['GingerModelForm', 
           'GingerForm',
           'GingerSearchModelForm',
           'GingerSearchForm',
           'GingerSafeEmptyTuple',
           'GingerFormMixin',
           'GingerSearchFormMixin',
           'GingerDataForm',
           'GingerDataModelForm']



class GingerSafeEmptyTuple(tuple):
    def __len__(self):
        return 1


class GingerFormMixin(object):

    failure_message = None
    success_message = None
    ignore_errors = False
    use_defaults = False

    def __init__(self, **kwargs):
        parent_cls = forms.Form if not isinstance(self, forms.ModelForm) else forms.ModelForm
        constructor = parent_cls.__init__
        keywords = set(inspect.getargspec(constructor).args)
        self.use_defaults = kwargs.pop("use_defaults", self.use_defaults)
        if "ignore_errors" in kwargs:
            self.ignore_errors = kwargs.pop("ignore_errors")
        context = {}
        for key in kwargs.copy():
            if key in keywords:
                continue
            value = kwargs.pop(key)
            context[key] = value
        super(GingerFormMixin, self).__init__(**kwargs)
        self.context = context
        self.merge_defaults()

    def field_range(self, first, last, step=None):
        keys = self.fields.keys()
        if first is not None and isinstance(first, six.string_types):
            try:
                first = keys.index(first)
            except ValueError:
                raise KeyError("%r is not a field for form %r" % (first, self.__class__.__name__))
        if last is not None and isinstance(last, six.string_types):
            try:
                last = keys.index(last)-1
            except ValueError:
                raise KeyError("%r is not a field for form %r" % (last, self.__class__.__name__))
        return self.iter_fields(keys[first:last:step])

    def iter_fields(self, names):
        return (self[field] for field in names)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.field_range(item.start, item.stop, item.step)
        return super(GingerFormMixin, self).__getitem__(item)

    def merge_defaults(self):
        if self.use_defaults:
            data = QueryDict('', mutable=True)
            if self.data:
                data.update(self.data)
            initial = self.initial_data
            for key in initial:
                if key in data:
                    continue
                value = initial[key]
                name = self.add_prefix(key)
                if value is not None:
                    if hasattr(value, "__iter__"):
                        data.setlistdefault(name, value)
                    else:
                        data.setdefault(name, value)
            self.data = data

    def process_context(self):
        context = self.context
        if not isinstance(self, GingerSearchFormMixin) and hasattr(self, "cleaned_data"):
            if hasattr(self, "save"):
                instance = self.save(commit=False)
                utils.model_update_from_dict(instance, context, many_to_many=True)
                context["instance"] = instance
            context["data"] = self.cleaned_data
        spec = inspect.getargspec(self.execute)
        if spec.varargs:
            raise ImproperlyConfigured("Form.execute cannot have variable arguments")
        if spec.keywords:
            return context
        return {k: context[k] for k in spec.args[1:] if k in context}

    @property
    def initial_data(self):
        fields = self.fields
        result = {}
        for name,field in six.iteritems(fields):
            data = self.initial.get(name, field.initial)
            if callable(data):
                data = data()
                if (isinstance(data, (datetime.datetime, datetime.time)) and
                        not getattr(field.widget, 'supports_microseconds', True)):
                    data = data.replace(microsecond=0)
            if data and isinstance(field, forms.MultiValueField):
                for i, f in enumerate(field.fields):
                    key = "%s_%s" % (name, i)
                    result[key] = data[i]
            elif data is not None:
                result[name] = data
        return result

    @property
    def result(self):
        self.is_valid()
        return self.__result

    def get_success_message(self):
        return self.success_message

    def get_failure_message(self):
        return self.failure_message

    def get_confirmation_message(self):
        return self.confirmation_message

    @classmethod
    def class_oid(cls):
        """
        Obfuscated class id
        :return: str
        """
        return utils.create_hash(utils.qualified_name(cls))

    @classmethod
    def is_submitted(cls, data):
        return data and (any(k in data for k in self.base_fields) or self.submit_name() in data)

    @classmethod
    def submit_name(cls):
        return "submit-%s" % cls.uid()

    def run(self):
        if not self.is_valid() and not self.ignore_errors:
            raise ValidationFailure(self)
        return self.result

    def full_clean(self):
        super(GingerFormMixin, self).full_clean()
        try:
            _ = self.__result
        except AttributeError:
            result = None
            if self.is_bound and (not self._errors or self.ignore_errors):
                context = self.process_context()
                try:
                    result = self.execute(**context)
                except forms.ValidationError as ex:
                    self.add_error(None, ex)
                finally:
                    self.__result = result

    #
    # def is_valid(self):
    #     func = super(GingerFormMixin, self).is_valid
    #     try:
    #         _ = self.result
    #     except AttributeError:
    #         pass
    #     else:
    #         return func()
    #     result = None
    #     if func() or self.ignore_errors:
    #         try:
    #             result = self.execute(**self.context)
    #         except forms.ValidationError as ex:
    #             self.add_error(None, ex)
    #         finally:
    #             self.__result = result
    #     return func()

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
    use_defaults = True

    def _post_clean(self):
        """
            This override is needed so as to avoid modelform validation during clean
        """

    def insert_null(self, field_name, label, initial=""):
        field = self.fields[field_name]
        if initial is None:
            initial = field.empty_value
        field.required = False
        field.initial = initial
        choices = list(field.choices)
        top = choices[0][0]
        if top == field.empty_value or not top:
            choices = choices[1:]
        choices.insert(0, (initial, label))
        field.choices = tuple(choices)

    def get_sort_field(self):
        from .fields import SortField
        try:
            return next(self[name] for name, f in six.iteritems(self.fields) if isinstance(f, SortField))
        except StopIteration:
            return None

    def get_queryset(self, **kwargs):
        return self.queryset

    def execute(self, **kwargs):
        return self.process_queryset_filters(**kwargs)

    def get_queryset_filter_names(self):
        return self.fields.keys()

    def process_queryset_filters(self, page=None, parameter_name="page",
                      page_limit=10, per_page=20, **kwargs):
        queryset = self.get_queryset(**kwargs)
        data = self.cleaned_data if self.is_bound else self.initial_data
        allowed = set(self.get_queryset_filter_names())
        for name, value in six.iteritems(data):
            if name not in allowed or not value:
                continue
            kwargs = {}
            field = self.fields[name]
            if hasattr(self, "handle_%s" % name):
                result = getattr(self,"handle_%s" % name)(queryset, value, data)
            elif hasattr(field, "handle_queryset"):
                result = field.handle_queryset(queryset, value, self[name])
            else:
                if isinstance(value, (tuple,list)):
                    name = '%s__in' % name
                kwargs[name] = value
                result = queryset.filter(**kwargs)
            if result is not None:
                queryset = result
        if page is not None:
            queryset = self.paginate(queryset, page,
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


class GingerDataFormMixin(GingerSearchFormMixin):

    def execute(self, **kwargs):
        result = super(GingerDataFormMixin, self).execute(**kwargs)
        schema_cls = self.get_dataset_class()
        dataset = schema_cls()
        self.load_dataset(dataset, result)
        self.process_dataset_filters(dataset)
        return dataset

    def load_dataset(self, dataset, data_source):
        dataset.extend(data_source)

    def process_dataset_filters(self, dataset, **kwargs):
        cleaned_data = self.cleaned_data if self.is_bound else self.initial_data
        for name in self.get_dataset_filter_names():
            value = cleaned_data.get(name)
            field = self.fields[name]
            if value is None or value == "":
                continue
            if hasattr(self, "handle_%s" % name):
                getattr(self,"handle_%s" % name)(dataset, value, cleaned_data)
            elif hasattr(field, "handle_dataset"):
                field.handle_dataset(dataset, value, self[name])
        sort_field = self.get_sort_field()
        if sort_field:
            dataset.sort_parameter_name = sort_field.html_name
        return dataset


    def get_dataset_class(self):
        try:
            return next(f.dataset_class for f in six.itervalues(self.fields)
                        if hasattr(f, "dataset_class"))
        except StopIteration:
            return self.dataset_class

    def get_dataset_filter_names(self):
        names = set(name for name, f in six.iteritems(self.fields)
                    if getattr(f, "process_list", False))
        names.update(getattr(self, "dataset_filters", ()))
        return names

    def get_queryset_filter_names(self):
        names = super(GingerDataFormMixin, self).get_queryset_filter_names()
        dataset_filters = set(self.get_dataset_filter_names())
        return [name for name in names if name not in dataset_filters]

    def to_json(self):
        result = self.run()
        return {
            "data": result.rows,
            "aggregates": result.aggregates.rows,
            "page": result.object_list if result.is_paginated() else None,
            "schema": [col.to_json() for col in result.columns]
        }


class GingerDataModelForm(GingerDataFormMixin, forms.ModelForm):
    pass


class GingerDataForm(GingerDataFormMixin, forms.Form):
    pass
