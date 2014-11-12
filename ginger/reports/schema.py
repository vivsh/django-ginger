

import itertools
from collections import OrderedDict
import inspect
import weakref


__all__ = ["Column", "DataSet"]


class Column(object):

    __position = 1

    def __init__(self, label=None, kind=None, model_attr=None):
        self.__position += 1
        Column.__position += 1
        self.label = label
        self.kind = kind
        self.model_attr = model_attr


class BoundColumn(object):

    def __init__(self, schema, name, position, column):
        self.schema = schema
        self.column = column
        self.name = name
        self.position = position
        self.kind = column.kind

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
        return {
            "name": self.name,
            "position": self.position,
            "kind": self.kind
        }

    def sort(self, key=None, reverse=False):
        i = self.position
        self.schema.rows.sort(reverse=reverse,
                              key=lambda row: key(row[i]) if key is not None else row[i])

    def build_link(self, request):
        return


def get_columns(schema):
    values = sorted(inspect.getmembers(schema,
                                       lambda _, value: isinstance(value, Column)),
                    key=lambda val: val[1].column.position)
    result = OrderedDict()
    for i, (name, column) in enumerate(values):
        col = BoundColumn(schema, i, name, column)
        result[col.name] = col
        result[i] = col
    return result


class DataSetBase(object):

    def __init__(self):
        self.__rows = []

    def sort(self, *args, **kwargs):
        self.rows.sort(*args, **kwargs)

    @property
    def rows(self):
        return self.__rows

    def format_cell(self, i, value):
        raise NotImplementedError

    def format_rows(self):
        formatter = self.format_cell
        for row in self.rows:
            yield (formatter(i, value) for i, value in enumerate(row))

    def append(self, data):
        self.rows.append(tuple(data))

    def to_json(self):
        return self.rows

    def extend(self, items):
        for d in items:
            self.append(d)

    def insert(self, i, data):
        row = tuple(data)
        self.rows.insert(i, row)

    def __getitem__(self, item):
        return self.rows[item]

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)


class DataAggregates(DataSetBase):

    def __init__(self, schema):
        super(DataAggregates, self).__init__()
        self.schema = weakref.ref(schema)

    def format_cell(self, i, value):
        return self.schema.format_cell(i, value)


class DataSet(DataSetBase):
    """
    List of tuples
    """

    def __init__(self):
        super(DataSet, self).__init__()
        self.__columns = get_columns(self)
        self.aggregates = DataAggregates(self)

    def format_cell(self, index, value):
        column = self.columns[index]
        kind = column.kind
        try:
            func = getattr(self, "format_%s" % kind)
        except AttributeError:
            return str(value)
        else:
            return func(value)


class ModelDataSet(DataSet):

    def __init__(self, object_list):
        super(ModelDataSet, self).__init__()
        self.object_list = object_list
        self.page = object_list if hasattr(object_list, "paginator") else None
        self._fill_rows(object_list)

    def is_paginated(self):
        return self.page is not None

    def _fill_rows(self, object_list):
        self.extend(self._make_row(obj) for obj in object_list)

    def _make_row(self, obj):
        result = []
        for column in self.columns:
            try:
                method = getattr(self, "prepare_%s" % column.name)
            except AttributeError:
                value = getattr(obj, column.model_attr or column.name)
            else:
                value = method(obj)
            result.append(value)
        return tuple(result)

