
import inspect
import copy
from collections import OrderedDict

from ginger.nav import Link
from ginger.utils import get_url_with_modified_params

__all__ = ['Formatter', 'FormattedTable', 'FormattedObject']


class Formatter(object):

    __position = 1

    def __init__(self, label=None, attr=None, hidden=False, sortable=True, variants=None):
        Formatter.__position += 1
        self.__position = Formatter.__position
        self.label = label
        self.hidden = hidden
        self.sortable = sortable
        self.attr = attr
        if variants is not None:
            if not isinstance(variants, (list, tuple)):
                variants = [variants]
            variants = set(variants)
        self.variants = variants

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

    def extract(self, name, source, owner=None):
        if owner is not None:
            method = 'prepare_%s' % name
            func = getattr(owner, method, None)
            if func:
                return func(source)
        parts = name.split("__")
        result = source
        while parts:
            item = parts.pop(0)
            if isinstance(result, dict):
                result = result[item]
            else:
                result = getattr(result, item)
        return result

    def render(self, name, source, owner):
        value = self.extract(name, source, owner)
        return self.format(value, name, source)

    @classmethod
    def extract_from(cls, source, variant=None):
        result = sorted(inspect.getmembers(source, lambda a: isinstance(a, Formatter)),
            key=lambda p: p[1].position)
        result = [p for p in result if p[1].variants is None or variant in p[1].variants]
        return result


class FormattedValue(object):

    def __init__(self, name, prop, source, attrs=None, owner=None):
        self.name = name
        self.prop = prop
        self.source = source
        self.__attrs = attrs
        self.__owner = owner

    def get_absolute_url(self):
        try:
            func = self.__owner.get_cell_url
        except AttributeError:
            return None
        else:
            return func(self)

    @property
    def attrs(self):
        return self.__attrs(self) if self.__attrs else {}

    @property
    def label(self):
        label = self.prop.label
        return label if label is not None else self.name.capitalize()

    @property
    def value(self):
        return self.prop.extract(self.name, self.source, self.__owner)

    def __getattr__(self, item):
        return getattr(self.prop, item)

    def __str__(self):
        return str(self.prop.format(self.value, self.name, self.source))


class FormattedObject(object):

    def __init__(self, obj, variant=None, **context):
        self.context = context
        self.variant = variant
        self.__prop_cache = OrderedDict((n,p) for (n,p) in Formatter.extract_from(self.__class__, variant=variant) if not p.hidden)
        self.source = obj
        data = self.data = OrderedDict()
        for name, prop in self.__prop_cache.items():
            data[name] = FormattedValue(name, prop, self.source, attrs=self.get_attrs, owner=self)

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __getitem__(self, item):
        try:
            return self.data[item]
        except KeyError:
            raise AttributeError(item)

    def __iter__(self):
        for name, prop in self.__prop_cache.items():
            yield self.data[name]

    def __len__(self):
        return len(self.__prop_cache)

    def __bool__(self):
        return len(self) > 0

    def get_attrs(self, value):
        return {}

    @classmethod
    def as_table(cls):
        props = dict(Formatter.extract_from(cls))
        for key in cls.__dict__:
            if key.startswith("prepare_"):
                props[key] = cls.__dict__[key]
        name = cls.__name__
        return type("%sTable"%name, (FormattedTable,), props)


class FormattedTableColumn(object):

    __inited = False

    def __init__(self, name, prop, table):
        self.name = name
        self.prop = prop
        self.table = table
        self.__inited = True

    @property
    def label(self):
        return self.prop.label or self.name.capitalize()

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

    def visible_columns(self):
        return [col for col in self.columns.values() if not col.hidden]

    def hidden_columns(self):
        return [col for col in self.columns.values() if col.hidden]

    def keys(self):
        return self.columns.keys()

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
        self.data = OrderedDict()
        for column in self.table.columns:
            self.data[column.name] = FormattedValue(column.name, column.prop, source,
                                                    attrs=self.table.get_cell_attrs,
                                                    owner=table)

    def __getitem__(self, item):
        return self.data[item]

    @property
    def object(self):
        return self.source

    @property
    def attrs(self):
        return self.table.get_row_attrs(self)

    def __iter__(self):
        for column in self.table.columns:
            yield self.data[column.name]

    def __len__(self):
        return len(self.table.columns)

    def __bool__(self):
        return len(self) > 0


class FormattedTable(object):

    def __init__(self, source, sort_key=None, sort_field=None, variant=None, **context):
        self.context = context
        self.variant = variant
        self.columns = FormattedTableColumnSet(self, Formatter.extract_from(self.__class__, variant=variant))
        self.source = source
        self.sort_field = sort_field
        self.sort_key = sort_key

    def build_links(self, request):
        data = request.GET
        for col in self.columns.visible_columns():
            if self.sort_key and self.sort_field:
                field = self.sort_field
                code = field.get_value_for_name(col.name)
                value = data.get(self.sort_name, "")
                reverse = value.startswith("-")
                if reverse:
                    value = value[1:]
                is_active = code == value
                next_value = "-%s" % code if not reverse and is_active else code
                mods = {self.sort_name: next_value}
            else:
                is_active = False
                reverse = False
                mods = {}
            url = get_url_with_modified_params(request, mods) if mods else None
            link = Link(content=col.label, url=url, is_active=is_active, reverse=reverse, sortable=col.sortable, column=col)
            yield link

    @property
    def object_list(self):
        return self.source

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