
from django.utils import six
import inspect


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


class MetaSchema(type):

    def __new__(self, bases, **attributes):
        for key, value in six.iteritems(attributes):
            if isinstance(value, Column):
                value.name = key
        return super(MetaSchema, self).__new__(self, bases, **attributes)



@six.add_metaclass(MetaSchema)
class Schema(object):

    def get_columns(self):
        return (value for key, value in
                inspect.getmembers(self, lambda name, value: isinstance(value, Column)))

    def select_columns(self, queryset):
        columns = []
        for col in self.get_columns():
            columns.append(col.db_column)
        return queryset.only(*columns)

    def to_json(self):
        return {
            "columns": [

            ]
        }


