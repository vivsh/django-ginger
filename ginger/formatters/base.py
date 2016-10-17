
import inspect
import copy
from collections import OrderedDict


__all__ = ['Formatter', 'FormattedTable', 'FormattedObject']


class Formatter(object):

    __position = 1

    def __init__(self, label=None, attr=None, hidden=False):
        Formatter.__position += 1
        self.__position = Formatter.__position
        self.label = label
        self.hidden = hidden
        self.attr = attr

    def copy(self):
        instance = copy.copy(self)
        Formatter.__position += 1
        instance.__position = Formatter.__position
        return instance

    @property
    def position(self):
        return self.__position

    def format(self, value, name, source):
        return str(value)

    def extract(self, name, source):
        method = 'prepare_%s' % name
        func = getattr(source, method, None)
        if func:
            return func(source)
        try:
            return getattr(source, name)
        except AttributeError:
            if isinstance(source, dict) and name in source:
                return source[name]
            raise

    def render(self, name, source):
        value = self.extract(name, source)
        return self.format(value, name, source)

    @classmethod
    def extract_from(cls, source):
        return sorted(inspect.getmembers(source, lambda a: isinstance(a, Formatter)),
            key=lambda p: p[1].position)


class FormattedValue(object):

    def __init__(self, name, prop, source, attrs=None):
        self.name = name
        self.prop = prop
        self.source = source
        self.__attrs = attrs

    @property
    def attrs(self):
        return self.__attrs(self) if self.__attrs else {}

    @property
    def label(self):
        label = self.prop.label
        return  label if label is not None else self.name.capitalize()

    @property
    def value(self):
        return self.prop.extract(self.name, self.source)

    def __getattr__(self, item):
        return getattr(self.prop, item)

    def __str__(self):
        return self.prop.format(self.value, self.name, self.source)

    def __repr__(self):
        return self.__str__()


class FormattedObject(object):

    def __init__(self, obj):
        self.__prop_cache = OrderedDict((n,p) for (n,p) in Formatter.extract_from(self.__class__) if not p.hidden)
        self.source = obj
        for name, prop in self.__prop_cache.items():
            setattr(self, name, FormattedValue(name, prop, self.source, self.get_attrs))

    def __iter__(self):
        for name, prop in self.__prop_cache.items():
            yield getattr(self, name)

    def __len__(self):
        return len(self.__prop_cache)

    def __bool__(self):
        return len(self) > 0

    def get_attrs(self, value):
        return {}

    @classmethod
    def as_table(cls):
        props = dict(Formatter.extract_from(cls))
        name = cls.__name__
        return type("%sTable"%name, (FormattedTable,), props)


class FormattedTableColumn(object):

    __inited = False

    def __init__(self, name, prop, table):
        self.name = name
        self.prop = prop
        self.table = table
        self.__inited = True

    def __setattr__(self, key, value):
        if self.__inited and key not in __dict__:
            setattr(self.prop, key, value)
        else:
            self.__dict__[key] = value

    def __getattr__(self, item):
        return getattr(self.prop, item)

    def __getitem__(self, item):
        return getattr(self.prop, item)

    def values(self):
        for obj in self:
            yield obj.value

    def __iter__(self):
        for obj in self.table.source:
            yield FormattedValue(self.name, self.prop, obj, self.table.get_cell_attrs)

    def __len__(self):
        return len(self.table.source)

    def __bool__(self):
        return len(self) > 0


class FormattedTableColumnSet(object):

    def __init__(self, table, values):
        self.columns = OrderedDict((n, FormattedTableColumn(n, p, table)) for n,p in values)

    def __iter__(self):
        for value in self.columns.values():
            yield value

    def __contains__(self, item):
        return item in self.columns

    def __getitem__(self, item):
        return self.columns[item]

    def __getattr__(self, item):
        return self.columns[item]

    def __len__(self):
        return len(self.columns)

    def __bool__(self):
        return len(self) > 0


class FormattedTableRow(object):

    def __init__(self, index, source, table, kind=None):
        self.index = index
        self.source = source
        self.table = table
        self.kind = kind
        for column in self.table.columns:
            setattr(self, column.name,
                    FormattedValue(column.name, column.prop, self.object, self.table.get_cell_attrs))

    @property
    def object(self):
        return self.source

    @property
    def attrs(self):
        return self.table.get_row_attrs(self)

    def __iter__(self):
        for column in self.table.columns:
            yield getattr(self, column.name)

    def __len__(self):
        return len(self.table.columns)

    def __bool__(self):
        return len(self) > 0


class FormattedTable(object):

    def __init__(self, source):
        self.columns = FormattedTableColumnSet(self, Formatter.extract_from(self.__class__))
        self.source = source

    def __iter__(self):
        index = 0
        for obj in self.source:
            yield FormattedTableRow(index, obj, self)
            index += 1

    def __len__(self):
        return len(self.source)

    def __bool__(self):
        return len(self) > 0

    def get_row_attrs(self, row):
        return {}

    def get_cell_attrs(self, cell):
        return {}

    def get_footer_rows(self):
        return ()