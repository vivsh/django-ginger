from __future__ import division

import itertools
import inspect
import weakref
from collections import OrderedDict
import collections
from django.utils import six
from ginger import ui
from ginger.utils import get_url_with_modified_params


__all__ = ["Column", "GingerDataSet"]


class Column(object):

    __position = 1

    def __init__(self, label=None, kind=None, model_attr=None, hidden=False):
        self.__position += 1
        Column.__position += 1
        self.label = label
        self.kind = kind
        self.model_attr = model_attr
        self.hidden = hidden

    @property
    def position(self):
        return self.__position


class BoundColumn(object):

    def __init__(self, schema, name, position, column):
        self.schema = schema
        self.column = column
        self.name = name
        self.position = position
        self.hidden = column.hidden

    def is_hidden(self):
        return self.hidden

    def toggle(self):
        return self.show() if self.is_hidden() else self.hide()

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    @property
    def kind(self):
        return self.column.kind

    @property
    def model_attr(self):
        return self.column.model_attr

    @property
    def label(self):
        return self.column.label or self.name.capitalize()

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

    def __repr__(self):
        return "BoundColumn<name: %s, position:  %s>"%(self.name, self.position)


class DataRow(object):

    __inited = False

    def __init__(self, owner, data):
        self.data = data
        self.owner = weakref.ref(owner)
        assert len(self.data) == len(self.columns)
        self.__inited = True

    @property
    def columns(self):
        return self.owner()._get_schema().columns

    def items(self):
        return self.cells(columns=True)

    def cells(self, columns=False):
        cols = self.columns.visible()
        formatter = self.owner()._format_cell
        for col in cols:
            i = col.position
            value = formatter(i, self.data[i])
            yield (col, value) if columns else value

    def __getattr__(self, item):
        try:
            col = self.columns[item]
        except KeyError:
            raise AttributeError(item)
        else:
            return self.data[col.position]

    def __setattr__(self, key, value):
        if not self.__inited:
            self.__dict__[key] = value
        else:
            try:
                col = self.columns[key]
            except KeyError:
                raise AttributeError(key)
            else:
                data = list(self.data)
                data[col.position] = value
                self.__dict__['data'] = tuple(data)

    def __iter__(self):
        """
        iterates over non-hidden columns only
        """
        for col in self.columns.visible():
            yield self.data[col.position]

    def __len__(self):
        return len(self.columns.visible())

    def __getitem__(self, item):
        col = self.columns[item]
        return self.data[col.position]

    def to_json(self):
        return self.data


class DataSetBase(object):

    def __init__(self):
        self.__rows = []
        self.object_list = None

    def _get_schema(self):
        raise NotImplementedError

    def sort(self, *args, **kwargs):
        self.rows.sort(*args, **kwargs)

    @property
    def rows(self):
        return self.__rows

    def _format_cell(self, i, value):
        raise NotImplementedError

    def empty_row(self):
        data = [None] * len(self._get_schema().columns)
        return self.append(data)

    def append(self, data):
        row = self._make_row(data)
        self.rows.append(row)
        return row

    def extend(self, items):
        self.object_list = items
        for d in items:
            self.append(d)

    def insert(self, i, data):
        row = self._make_row(data)
        self.rows.insert(i, row)

    def _make_row(self, obj):
        if isinstance(obj, DataRow):
            return obj
        if not inspect.isgenerator(obj) and not isinstance(obj, collections.Sequence):
            result = []
            for column in self.columns:
                attr = column.model_attr or column.name
                try:
                    method = getattr(self, "prepare_%s" % column.name)
                except AttributeError:
                    if isinstance(obj, collections.Mapping):
                        value = obj[attr]
                    else:
                        value = getattr(obj, attr)
                else:
                    value = method(obj)
                result.append(value)
        else:
            result = obj
        return DataRow(self, tuple(result))

    def to_json(self):
        return self.rows

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

    def _format_cell(self, i, value):
        return self._get_schema()._format_cell(i, value, True)

    def _get_schema(self):
        return self.schema()


class DictList(list):

    def __getitem__(self, item):
        if isinstance(item, six.string_types):
            try:
                return next(col for col in self if item == col.name)
            except StopIteration:
                raise KeyError("%r is not a key" % item)
        return super(DictList, self).__getitem__(item)

    def visible(self):
        return [col for col in self if not col.is_hidden()]


class GingerDataSet(DataSetBase):
    """
    List of tuples
    """

    def __init__(self, object_list=None):
        super(GingerDataSet, self).__init__()
        self.__columns = self.setup_columns()
        self.aggregates = DataAggregates(self)
        if object_list:
            self.extend(object_list)

    def is_paginated(self):
        return hasattr(self.object_list, "paginator")

    def _get_schema(self):
        return self

    @classmethod
    def get_column_dict(cls):
        values = sorted(inspect.getmembers(cls,
                                       lambda value: isinstance(value, Column)),
                    key=lambda val: val[1].position)
        return OrderedDict(values)

    def setup_columns(self):
        column_dict = self.get_column_dict()
        result = DictList()
        for i, (name, column) in enumerate(six.iteritems(column_dict)):
            col = BoundColumn(self, name, i, column)
            result.append(col)
        return result

    @property
    def columns(self):
        return self.__columns

    def _format_cell(self, index, value, aggregate=False):
        column = self.columns[index]
        suffixes = (column.name, column.kind)
        for suffix in suffixes:
            func = getattr(self, "render_%s" % suffix, None)
            if func:
                return func(value, index, aggregate)
        return str(value) if value is not None else ""

    def build_links(self, request):
        data = request.GET
        sort_name = getattr(self, "sort_parameter_name", None)
        for col in self.columns.visible():
            if sort_name:
                value = data.get(sort_name, "")
                reverse = value.startswith("-")
                if reverse:
                    value = value[1:]
                is_active = col.name == value
                next_value = "-%s" % col.name if not reverse and is_active else col.name
                mods = {sort_name: next_value}
            else:
                is_active = False
                reverse = False
                mods = {}
            url = get_url_with_modified_params(request, mods)
            yield ui.Link(content=col.label, url=url, is_active=is_active, reverse=reverse)

    def export_csv(self, response, header=False, hidden=True):
        import csv
        writer = csv.writer(response)
        columns = tuple(col for col in self.columns if hidden or not col.is_hidden())
        if header:
            writer.writerow([col.label for col in columns])
        for row in self.rows:
            writer.writerow([row[col.position] for col in columns])

    def export_xlsx(self, response, header=False, hidden=True):
        from openpyxl import Workbook
        book = Workbook(encoding="utf-8")
        columns = tuple(col for col in self.columns if hidden or not col.is_hidden())
        sheet = book.create_sheet(index=0)
        if header:
            sheet.append([col.label for col in columns])
        for row in self.rows:
            sheet.append([row[col.position] for col in columns])
        book.save(response)

    @staticmethod
    def export_formats():
        return (
            ("csv", "CSV"),
            ("xlsx", "XLSX")
        )