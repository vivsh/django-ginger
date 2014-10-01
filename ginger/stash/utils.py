
from django.db.models.sql.where import WhereNode, OR, AND
import inspect
from . import compat
from .compat import six

__all__ = ['get_query_filter', 'get_cache_key', 'make_key_from_args', 'get_cache_key_for_queryset']

kwargs_sentinel = object()  

class QueryFilterError(Exception):
    pass

LookUps = {
    "in": lambda value, col: col in value,
    "exact": lambda value, col: col == value,
    "iexact": lambda value, col: isinstance(col, six.string_types) and (value.lower() == col.lower()),
    "isnull": lambda value, col: (col is None) == value,
    "startswith": lambda value, col: col and col.startswith(value),
    "endswith": lambda value, col: col and col.endswith(value),
    "contains": lambda value, col: isinstance(col, six.string_types) and (value in col),
    "icontains": lambda value, col: isinstance(col, six.string_types) and (value.lower() in col.lower()),

    "lt": lambda value, col: col < value,
    "lte": lambda value, col: col <= value,
    
    "gt": lambda value, col: col >= value,
    "gte": lambda value, col: col >= value,
    "eq": lambda value, col: col == value,
}

def lookup_func(constraint, lookup, value):
    try:
        op = LookUps[lookup]
    except KeyError:
        raise QueryFilterError("No operator exists for %r"%lookup)
    name = constraint.field.attname
    def func(ins):
        col = getattr(ins, name, None)
        return op(value, col)
    return func

def where_func(model, where):
    connector = any if where.connector == OR else all
    predicates = []
    for node in where.children:
        if isinstance(node, WhereNode):
            func = where_func(model, node)
        elif isinstance(node, tuple):
            constraint, lookup, _, value = node
            if model != constraint.field.model:
                raise QueryFilterError("Cannot handle related lookups: %r"%constraint.field.name)
            func = lookup_func(constraint, lookup, value)
        else:
            raise QueryFilterError("Cannot convert %r to a function"%where)
        predicates.append(func)
    result = lambda ins: connector( func(ins) for func in predicates )
    if where.negated:
        return lambda ins: not result(ins)
    return result

def get_query_filter(query):
    model = query.model
    where = query.where
    try:
        return where_func(model, where)
    except QueryFilterError:
        return 

def make_key_from_args(*args, **kwargs):
    return args + tuple(sorted(kwargs.items()))
    
def get_cache_key(*args, **kwargs):
    key = make_key_from_args(*args, **kwargs)
    md5 = compat.md5()
    for val in key:
        md5.update(repr(val))
    return md5.hexdigest()

def get_cache_key_for_function(func, *args, **kwargs):
    name = "%s.%s"%(inspect.getsourcefile(func), func.__name__)
    return get_cache_key(name, *args, **kwargs)

def get_cache_key_for_queryset(queryset, op=None):
    clone = queryset.query.clone()
    sql, params = clone.get_compiler(using=queryset.db).as_sql()
    stmt = sql % params
    if op:
        stmt = "%s:%r"%(stmt, op)
    return get_cache_key(stmt)
    
    