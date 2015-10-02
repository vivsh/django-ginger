from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q, ObjectDoesNotExist
import operator


__all__ = ['ListQuerySet']


class And(object):

    def __init__(self, funcs):
        self.funcs = list(funcs)

    def test(self, *args, **kwargs):
        return all(func(*args, **kwargs) for func in self.funcs)

    def __call__(self, *args, **kwargs):
        return self.test(*args, **kwargs)

    def __len__(self):
        return len(self.funcs)


class Or(And):

    def test(self, *args, **kwargs):
        return any(func(*args, **kwargs) for func in self.funcs)


class Not(And):

    def __init__(self, func):
        self.func = func

    def __nonzero__(self):
        return bool(self.func)

    def test(self, *args, **kwargs):
        if self:
            return not bool(self.func(*args, **kwargs))
        return True


class Lookup(object):

    def __init__(self, key, value):
        self.value = value
        parts = key.split("__", 1)
        self.attr = parts.pop(0)
        if not parts:
            op = "exact"
        else:
            op = parts.pop()
        func = getattr(self, "check_%s" % op, None)
        if func is None:
            func = self.getattr
            self.value = Lookup(op, value)
        self.func = func

    def check(self, first, second):
        return self.func(first, second)

    def __call__(self, arg):
        first = getattr(arg, self.attr)
        if callable(self.value):
            return self.value(first)
        else:
            second = self.value
        return self.check(first, second)

    def getattr(self, first, second):
        return self.check_exact(getattr(first, self.attr), second)

    def check_startswith(self, first, second):
        return first.startswith(second)

    def check_istartswith(self, first, second):
        return first.lower().startswith(second.lower())

    def check_endswith(self, first, second):
        return first.startswith(second)

    def check_iendswith(self, first, second):
        return first.lower().endswith(second.lower())

    def check_contains(self, first, second):
        return first in second

    def check_exact(self, obj, value):
        return obj == value

    def check_gte(self, first, second):
        return first >= second

    def check_lte(self, first, second):
        return first <= second

    def check_gt(self, first, second):
        return first > second

    def check_lt(self, first, second):
        return first < second

    def check_isnull(self, first, second):
        return (first is None) == second


class ListQuerySet(object):

    def __init__(self, collection):
        self.collection = collection
        self.conditions = []
        self.ordering = ()
        self._cache = None

    def copy(self):
        ins = self.__class__(self.collection)
        ins.conditions.extend(self.conditions)
        return ins

    def order_by(self, *attrs):
        ins = self.copy()
        ins.ordering = attrs
        return ins

    def _resolve_q(self, obj):
        result = []
        for c in obj.children:
            if isinstance(c, Q):
                result.append(self._resolve_q(c))
            else:
                result.append(Lookup(*c))
        result = Or(result) if obj.connector == Q.OR else And(result)
        return result if not obj.negated else Not(result)

    def filter(self, *args, **kwargs):
        ins = self.copy()
        ins.conditions.append(And(map(self._resolve_q, args)))
        ins.conditions.extend(Lookup(k, v) for k,v in kwargs.iteritems())
        return ins

    def exclude(self, *args, **kwargs):
        ins = self.copy()
        if args:
            ins.conditions.append(Not(And(map(self._resolve_q, args))))
        if kwargs:
            ins.conditions.append(Not(And([Lookup(k, v) for k,v in kwargs.iteritems()])))
        return ins

    def _sort(self, values):
        for o in reversed(self.ordering):
            attr = o
            reverse = False
            if o.startswith("-"):
                attr = o[1:]
                reverse = True
            values.sort(reverse=reverse, key=operator.attrgetter(attr))
        return values

    def __len__(self):
        return len(self.all())

    def count(self):
        return len(self)

    def all(self):
        if self._cache is None:
            self._cache = result = filter(And(self.conditions), self.collection)
            if self.ordering:
                self._sort(result)
        return self._cache

    def get(self, *args, **kwargs):
        result = self.filter(*args, **kwargs).all()
        if not result:
            raise ObjectDoesNotExist
        if len(result) > 1:
            raise MultipleObjectsReturned
        return result[0]

    def update(self, **kwargs):
        result = []
        for obj in self.all():
            for k, v in kwargs.iteritems():
                setattr(obj, k, v)
            result.append(obj)
        return result


class Money(object):
    def __init__(self, amount):
        self.amount = amount

class Boy(object):

    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.money = Money(age * 12)

    def __repr__(self):
        return "Boy(%r,%r)" % (self.name, self.age)

if __name__ == '__main__':
    values = [Boy("Ram", 29), Boy("Shyam", 30), Boy("Pico", 12), Boy("Ram", 42)]
    qs = ListQuerySet(values)
    print(qs.filter(money__amount=360).order_by("name", "-age").get())

