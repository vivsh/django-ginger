
import itertools
from . import codes

__all__ = ['Module']



class _Base(object):

    def _convert(self, obj):
        func = self._convert
        if isinstance(obj, (tuple, list)):
            return obj.__class__(func(o) for o in obj)
        if isinstance(obj, dict):
            return obj.__class__((k, func(o)) for k,o in obj.items())
        return obj._obj if isinstance(obj, _Base) else obj


class _Def(_Base):

    def __init__(self, obj):
        self._obj = obj

    def __call__(self, stmt, *args, **kwargs):
        args, kwargs = self._convert((args, kwargs))
        indentation = 0
        first = True
        for ln in stmt.splitlines():
            if first and not ln.strip():
                continue
            if first:
                first = False
                indentation = sum(1 for _ in itertools.takewhile(lambda c: c.isspace(), ln))
            ln = ln[indentation:]
            self._obj.add(codes.Stmt(ln, *args, **kwargs))
        return self


class _Class(_Base):

    def __init__(self, obj):
        self._obj = obj

    def Def(self, *args, **kwargs):
        args, kwargs = self._convert((args, kwargs))
        obj = codes.Function(*args, **kwargs)
        self._obj.add(obj)
        return _Def(obj)


class Module(_Class):

    def __init__(self, module):
        self._obj = codes.Module(module)

    def Class(self, *args, **kwargs):
        args, kwargs = self._convert((args, kwargs))
        obj = codes.Class(*args, **kwargs)
        self._obj.add(obj)
        return _Class(obj)

    def save(self):
        return self._obj.save()

