
from django.utils import six
from collections import OrderedDict
import inspect
import operator


class Column(object):

    __position = 1

    def __init__(self, **kwargs):
        self.__position += 1
        Column.__position += 1
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

    @property
    def db_column(self):
        return self.name

    def to_json(self):
        return


class BoundColumn(object):

    def __init__(self, schema, column):
        self.schema = schema
        self.column = column

    @property
    def position(self):
        return self.column.position

    def __getattr__(self, name):
        return getattr(self.column, name)


class MetaSchema(type):

    def __new__(self, bases, **attributes):
        for key, value in six.iteritems(attributes):
            if isinstance(value, Column):
                value.name = key
        return super(MetaSchema, self).__new__(self, bases, **attributes)


@six.add_metaclass(MetaSchema)
class Schema(object):

    def __new__(cls, *args, **kwargs):
        obj = super(Schema, cls).__new__(cls, *args, **kwargs)
        obj.columns = OrderedDict(
            sorted(
                six.moves.map(
                    lambda o: (o.name, BoundColumn(obj, o)), obj.get_columns()
                ),
                key=operator.attrgetter("position")
            )
        )
        return obj

    def get_columns(self):
        return (value for key, value in
                inspect.getmembers(self, lambda name, value: isinstance(value, Column)))

    def select_columns(self, queryset):
        columns = []
        for col in six.itervalues(self.columns):
            columns.append(col.db_column)
        return queryset.only(*columns)

    def __getitem__(self, item):
        return self.columns[item]

    def to_json(self):
        return {
            "columns": six.moves.map(self.get_columns(), operator.methodcaller("to_json"))
        }


