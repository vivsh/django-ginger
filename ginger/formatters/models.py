from collections import OrderedDict

from django.utils import six
from django.db import models
from .formatters import *
from .base import FormattedObject, FormattedTable
from django.conf import settings


__all__ = ['FormattedModel', 'FormattedModelTable']


FORMATTER_MAPPING = {
    models.DateTimeField: DateTimeFormatter,
    models.DateField: DateFormatter,
    models.TimeField: TimeFormatter
}


FORMATTER_MAPPING.update(getattr(settings, 'FIELD_FORMATTERS', {}))


def get_formatter_for_field(field, options=None):
    try:
        return getattr(field, 'get_formatter')()
    except AttributeError:
        label = field.verbose_name.title()
        label = getattr(options, 'labels', {}).get(field.name, label)
        if field.choices:
            result = ChoiceFormatter(label=label)
        else:
            result = FORMATTER_MAPPING.get(field.__class__, Formatter)(label=label)
        return result


def get_formatters_for_model(model_class, fields=None, exclude=None, options=None):
    meta = model_class._meta
    field_map = OrderedDict((f.name, f) for f in meta.get_fields() if f.concrete and not f.auto_created)
    if fields is None:
        fields = list(field_map.keys())
    if exclude:
        exclude = set(exclude)
        fields = filter(lambda f: f.name not in exclude, fields)
    result = [(f, get_formatter_for_field(field_map[f], options)) for f in fields if f in field_map]
    return result


class MetaFormattedModel(type):

    def __init__(cls, name, bases, attrs):
        super(MetaFormattedModel, cls).__init__(name, bases, attrs)
        meta = getattr(cls, 'Meta', None)
        if not meta:
            return
        model = meta.model

        for name, formatter in get_formatters_for_model(model, fields=getattr(meta, 'fields', None),
                                                        exclude=getattr(meta, 'exclude', None),
                                                        options=meta):
            setattr(cls, name, formatter)


@six.add_metaclass(MetaFormattedModel)
class FormattedModel(FormattedObject):
    pass


@six.add_metaclass(MetaFormattedModel)
class FormattedModelTable(FormattedTable):

    def get_cell_url(self, cell):
        obj = cell.source
        url = getattr(obj, 'get_absolute_url', None)
        if url:
            return url()
        return None
