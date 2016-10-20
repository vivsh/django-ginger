
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


def get_formatter_for_field(field):
    try:
        return getattr(field, 'get_formatter')()
    except AttributeError:
        if field.choices:
            return ChoiceFormatter()
        return FORMATTER_MAPPING.get(field, Formatter)()


def get_formatters_for_model(model_class, fields=None, exclude=None):
    meta = model_class._meta
    field_map = {f.name: f for f in meta.get_fields() if f.concrete and not f.auto_created}
    if fields is None:
        fields = list(field_map.keys())
    if exclude:
        exclude = set(exclude)
        fields = filter(lambda f: f.name not in exclude, fields)
    return [(f, get_formatter_for_field(field_map[f])) for f in fields if f in field_map]


class MetaFormattedModel(type):

    def __init__(cls, name, bases, attrs):
        super(MetaFormattedModel, cls).__init__(name, bases, attrs)
        meta = getattr(cls, 'Meta', None)
        if not meta:
            return
        model = meta.model

        for name, formatter in get_formatters_for_model(model, fields=getattr(meta, 'fields', None),
                                                        exclude=getattr(meta, 'exclude', None)):
            setattr(cls, name, formatter)


@six.add_metaclass(MetaFormattedModel)
class FormattedModel(FormattedObject):
    pass


@six.add_metaclass(MetaFormattedModel)
class FormattedModelTable(FormattedTable):
    pass