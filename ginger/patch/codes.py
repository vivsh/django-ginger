import itertools
import inspect
import warnings

from .import sources
from .import utils



def indent(line, indentation):
    return utils.set_indentation(line, indentation)



class Code(object):

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.children = []

    @property
    def vertical_gap(self):
        parent = self.parent
        source = self.source
        gap = 2 if isinstance(parent, Module) else 1
        if isinstance(self, Class):
            gap = 2
        if source and source.is_first:
            gap = 0
        return gap

    def can_export(self, obj):
        return Exporter.can_export(obj)

    @property
    def local_name(self):
        parts = [self.name]
        parent = self.parent
        while parent and not isinstance(parent, Module):
            parts.insert(0, parent.name)
            parent = parent.parent
        return ".".join(parts)

    @property
    def root(self):
        return self.parent.root

    @property
    def full_name(self):
        names = []
        if self.parent:
            names.append(self.parent.full_name)
        names.append(self.name)
        return ".".join(names)

    @property
    def source(self):
        return sources.find(self.filename, self.full_name)

    def patch(self):
        return

    def reload(self):
        self.parent.reload()

    def save(self):
        obj = self.code
        self.export(self)
        if obj is None and self.source is None:
            source = self.parent.source
            source.add_child(self, gap=self.vertical_gap)
            source.save()
        else:
            self.patch()
            warnings.warn("%s already exists" % self.full_name)
            self.save_children()

    def save_children(self):
        for child in self.children:
            child.save()
        if self.children:
            self.source.remove_pass()

    def export(self, obj):
        return self.parent.export(obj)

    @property
    def filename(self):
        return self.parent.filename

    @property
    def code(self):
        name = self.name
        if name is not None:
            attr = getattr(self.parent.code, name, None)
        else:
            attr = None
        return attr

    def exists(self):
        return self.code is not None


class Value(object):

    parent = None

    def __init__(self, value, parent=None):
        super(Value, self).__init__()
        self.value = value if not isinstance(value, Value) else value.value
        self.parent = parent

    def export(self, obj):
        return self.parent.export(obj)

    def render(self, indentation=0):
        if isinstance(self.value, str):
            return repr(self.value)
        if isinstance(self.value, (float, int)):
            return str(self.value)
        result = self.export(self.value)
        return result if not isinstance(result, (list, tuple)) else repr(result)

    def __str__(self):
        return self.render()


class Decorator(object):

    def __init__(self, value):
        self.name = value

    def render(self, indentation=0):
        line = "@%s\n" % self.name
        return indent(line, indentation)


class Stmt(Code):

    name = None
    parent = None

    def __init__(self, code, *args, **kwargs):
        super(Stmt, self).__init__(None)
        self.value = code
        self.args = tuple(args)
        self.kwargs = kwargs

    def full_name(self):
        return None

    @property
    def source(self):
        return None

    def render(self, indentation=0):
        stmt = self.value.format(*self.export(self.args), **self.export(self.kwargs))
        value = "%s\n" % stmt
        return indent(value, indentation)


class Assign(Code):

    def __init__(self, name, value):
        super(Assign, self).__init__(name)
        self.value = Value(value, self)

    def render(self, indentation=0):
        value = str(self.value)
        line = "%s = %s" % (self.name, value)
        return indent(line, indentation)


class Block(Code):

    def add(self, code):
        if not hasattr(code, 'render'):
            code = Stmt(code)
        if code.parent:
            code.parent.children.remove(code)
        code.parent = self
        self.children.append(code)

    def get_children(self):
        children = self.children[:]
        if not children:
            stmt = Stmt("pass")
            stmt.parent = self
            children.append(stmt)
        return children


class Function(Block):

    def __init__(self, name, args=None, varargs=None, varkw=None,
                 defaults=None, decorators=None):
        super(Function, self).__init__(name)
        self.args = args or ()
        self.varargs = varargs
        self.varkw = varkw
        self.defaults = defaults or {}
        self.decorators = decorators or []

    def save_children(self):
        pass

    def patch(self):
        source = self.source
        source.set_decorators(self.get_decorators())

    def get_decorators(self):
        decorators = map(self.export, self.decorators)
        return decorators

    @property
    def method(self):
        if self.parent and isinstance(self.parent, Class):
            decorators = set(self.get_decorators())
            if "staticmethod" in decorators:
                return "static"
            if "classmethod" in decorators:
                return "class"
            return "instance"

    def get_signature(self):
        params = []
        defaults = {k: self.export(v) for (k, v) in self.defaults.items()}
        if self.method == "class":
            params.append("cls")
        elif self.method == "instance":
            params.append("self")
        for a in self.args:
            if a in defaults:
                params.append("%s=%s" % (a, defaults[a]))
            else:
                params.append(a)
        if self.varargs:
            params.append("*%s"%self.varargs)
        if self.varkw:
            params.append("**%s"%self.varkw)
        return "def %s(%s):" % (self.name, ", ".join(params))

    def render(self, indentation=0):
        code = self.code
        if code:
            return ""
        decorators = self.get_decorators()
        decorators = "".join(Decorator(c).render(indentation) for c in decorators)
        head = indent(self.get_signature(), indentation)
        children = self.get_children()
        body = "".join(c.render(indentation+4) for c in children)
        return "%s%s\n%s" % (decorators, head, body)


class Class(Block):

    def __init__(self, name, bases=None, decorators=None):
        if inspect.isclass(name):
            cls = name
            name = cls.__name__
            if bases is None:
                bases = cls.__bases__
        super(Class, self).__init__(name)
        self.bases = bases or [object]
        self.decorators = decorators or []

    def get_decorators(self):
        return map(self.export, self.decorators)

    def get_signature(self):
        bases = map(self.export, self.bases)
        return "class %s(%s):" % (self.name, ", ".join(bases))

    def patch(self):
        source = self.source
        source.set_signature(self.get_signature())
        source.set_decorators(self.get_decorators())

    def render(self, indentation=0):
        children = self.get_children()
        signature = self.get_signature()
        head = indent(signature, indentation)
        content = "\n".join(c.render(indentation+4) for c in children)
        decorators = "".join(Decorator(d).render(indentation) for d in self.get_decorators())
        return "%s%s\n\n%s" % (decorators, head, content)


class Exporter(object):

    def __init__(self, module):
        self.module = module
        self._aliases = {}
        self._exports = {}
        self._imports = []

    @staticmethod
    def can_export(obj):
        if isinstance(obj, Block):
            return True
        if inspect.ismodule(obj):
            return True
        if inspect.isfunction(obj):
            return True
        if inspect.isclass(obj):
            return True
        return False

    def find_export(self, name, obj):
        module = self.module
        if hasattr(module, name):
            value = getattr(module, name)
            if value is obj:
                return name
        for obj_name, obj_value in itertools.chain(inspect.getmembers(module, self.can_export),
                                                    ((v, k) for k, v in self._exports.items())):
            if getattr(obj_value, name, None) is obj:
                return "%s.%s" % (obj_name, name)

    def get_export_name(self, name, obj):
        module = self.module
        i = 0
        key = name
        while True:
            value = getattr(module, key, None)
            if value is obj or value is None:
                return key
            i += 1
            key = "%s%s" % (name, i)

    def add(self, obj):
        builtins = utils.builtins()
        exports = self._exports
        if obj in exports:
            return exports[obj]
        if isinstance(obj, Block):
            if obj.root is self.module:
                exports[obj] = obj.local_name
                return obj.local_name
            else:
                return self.add(obj.code)
        name = obj.__name__.split(".")[-1]
        if getattr(builtins, name, None) is obj:
            return name
        alias = self.find_export(name, obj)
        if alias is None:
            if inspect.ismodule(obj):
                name = self.get_export_name(name, obj)
                full_name = obj.__name__
                basename = full_name[:-len(name)-1]
                self._aliases[name] = (basename, name)
            elif inspect.isfunction(obj):
                obj_module = inspect.getmodule(obj)
                module_name = inspect.getmodulename(inspect.getsourcefile(obj))
                full_name = obj_module.__name__
                basename = full_name[:-len(module_name)-1]
                m = self.find_export(module_name, obj_module)
                if not m:
                    m = self.get_export_name(module_name, obj_module)
                self._aliases[m] = (basename, module_name)
                exports[obj_module] = m
                name = "%s.%s" % (m, name)
            else:
                obj_module = inspect.getmodule(obj)
                obj_name = self.get_export_name(name, obj)
                self._aliases[obj_name] = (obj_module.__name__, name)
                exports[obj] = obj_name
                name = obj_name
        else:
            name = alias
        exports[obj] = name
        return name

    def iter_imports(self):
        history = set()
        builtins = utils.builtins()
        module = self.module
        for from_, name, alias in self._imports:
            yield from_, name, alias
        for obj, name in self._exports.items():
            if isinstance(obj, Code):
                continue
            alias = name.split(".", 1)[0]
            if alias in history or hasattr(module, alias):
                continue
            if alias in self._aliases:
                from_, name = self._aliases[alias]
            else:
                from_ = ""
            if from_ == builtins.__name__:
                continue
            history.add(alias)
            if alias == name:
                alias = ""
            yield from_, name, alias

    def import_statements(self):
        stmts = []
        for imp in self.import_strings():
            stmts.append(Stmt(imp))
        return stmts

    def import_strings(self):
        for from_, name, alias in self.iter_imports():
            tail = " as %s"%alias if alias else ""
            if from_:
                stmt = "from %s import %s%s" % (from_, name, tail)
            else:
                stmt = "import %s%s" % (name, tail)
            yield stmt


class Module(Block):

    def __init__(self, module):
        self.code_obj = module
        self._filename = inspect.getsourcefile(module)
        name = module.__name__.split(".")[-1]
        super(Module, self).__init__(name)
        self.exporter = Exporter(module)

    @property
    def root(self):
        return self.code

    def export(self, obj):
        if isinstance(obj, dict):
            return {k: self.export(v) for (k, v) in obj.items()}
        if isinstance(obj, (tuple, list)):
            return obj.__class__(self.export(o) for o in obj)
        if not self.can_export(obj):
            return str(obj)
        return self.exporter.add(obj)

    def save(self):
        super(Module, self).save()
        for stmt in self.exporter.import_statements():
            stmt.parent = self
            self.source.prepend(stmt)
        self.source.save()
        self.reload()

    def reload(self):
        self.code_obj = reload(self.code_obj)

    @property
    def imports(self):
        return self.exporter.import_statements()

    @property
    def filename(self):
        return self._filename

    @property
    def code(self):
        return self.code_obj

    def render(self):
        indentation = 0
        children = self.get_children()
        content = "\n\n".join(c.render(indentation+4) for c in children)
        return content


if __name__ == '__main__':
    import sample
    mod = Module(sample)
    mod.export(object)
    print(list(mod.exporter.import_strings()))


