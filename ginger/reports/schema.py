
import weakref
import itertools
from django.utils import six
from collections import OrderedDict
import inspect
import operator


__all__ = ["Column", "DataSet"]


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


class BoundColumn(object):

    def __init__(self, schema, name, position, column):
        self.schema = schema
        self.column = column
        self.name = name
        self.position = position

    def __getattr__(self, name):
        return getattr(self.column, name)

    def __iter__(self):
        pos = self.position
        data = self.schema
        for row in data:
            yield row[pos]

    def __len__(self):
        return len(self.schema)

    def __getitem__(self, item):
        if type(item) == slice:
            return itertools.islice(self, item.start)
        return next(itertools.dropwhile(lambda i, _: i < item, enumerate(self)))

    def to_json(self):
        return self.schema.column_to_json(self)


def get_columns(schema):
    values = sorted(inspect.getmembers(schema,
                                       lambda _, value: isinstance(value, Column)),
                    key=lambda val: val[1].column.position)
    for i, (name, column) in enumerate(values):
        col = BoundColumn(schema, i, name, column)
        yield col.name, col


class DataSet(object):
    """
    List of tuples
    """

    @property
    def columns(self):
        try:
            return self.__columns
        except AttributeError:
            self.__columns = get_columns(self)
            return self.__columns

    @property
    def rows(self):
        try:
            return self.__rows
        except AttributeError:
            self.__rows = []
            return self.__rows

    def append(self, data):
        row = self.make_row(data)
        self.data.append(row)

    def make_row(self, data):
        return tuple(data)

    def column_to_json(self, col):
        return {
            "name": col.name,
            "label": col.label
        }

    def to_json(self):
        return {
            "data": self.rows,
            "columns": self.columns,
            "page": self.page
        }

    def extend(self, items):
        for d in items:
            self.append(d)

    def insert(self, i, data):
        row = self.make_row(data)
        self.rows.insert(i, row)

    def __getitem__(self, item):
        return self.rows[item]

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)

    def to_json(self):
        return {
            "schema": six.moves.map(self.schema, operator.methodcaller("to_json"))
        }


class QueryDataSet(DataSet):

    def __init__(self, object_list):
        super(QueryDataSet, self).__init__()
        self.object_list = object_list
        self.page = object_list if hasattr(object_list, "paginator") else None
        self.extractors = []

    def make_row(self, data):
        columns = self.columns
        attr_name = ""
        return
