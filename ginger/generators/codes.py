
import inspect
import warnings


def insert_content(filename, line_num, content):
    lines = open(filename).read().splitlines(True)
    lines.insert(line_num, content)
    open(filename, "w").writelines(lines)
    return


def indent(line, indentation, tabwidth=4):
    line = line.lstrip()
    pad = " "*indentation*tabwidth
    return "%s%s" % (pad, line)


class Code(object):
    def __init__(self, name):
        self.name = name

    def render(self):
        return

    def __str__(self):
        return self.render()


class Stmt(object):

    name = None

    def __init__(self, code):
        self.code = code

    def render(self, indentation):
        return indent(self.code+"\n", indentation)


class Assign(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def render(self, indentation=0):
        line = "%s = %s" % (self.name, self.value)
        return indent(line, indentation)


class Decorator(object):

    def __init__(self, value):
        self.value = value

    def render(self, indentation=0):
        line = "@%s\n" % self.value
        return indent(line, indentation)


class Block(object):

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.children = []
        self.imports = []

    def export(self, *args, **kwargs):
        self.parent.export(*args, **kwargs)

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

    def add(self, code):
        if not hasattr(code, 'render'):
            code = Stmt(code)
        code.parent = self
        self.children.append(code)

    @property
    def span(self):
        code = self.code
        if code:
            lines, num = inspect.getsourcelines(code)
            return num, num+len(lines)
        else:
            first, last = self.parent.span
            return last, last

    def get_children(self):
        return self.children

    def save(self):
        return


class Function(Block):

    def __init__(self, name, args=None, varargs=None, varkw=None,
                 defaults=None, method=None, decorators=None):
        super(Function, self).__init__(name)
        self.args = args or ()
        self.varargs = varargs
        self.varkw = varkw
        self.defaults = defaults or {}
        self.method = method
        self.decorators = decorators or []

    def render(self, indentation=0):
        code = self.code
        if code:
            return ""
        params = []
        defaults = self.defaults
        decorators = list(self.decorators)
        if self.method == "class":
            params.append("cls")
            decorators.append("classmethod")
        elif self.method == "instance":
            params.append("self")
        elif self.method == "static":
            decorators.append("staticmethod")
        for a in self.args:
            if a in defaults:
                params.append("%s=%s"%(a, defaults[a]))
            else:
                params.append(a)
        if self.varargs:
            params.append("*%s"%self.varargs)
        if self.varkw:
            params.append("**%s"%self.varkw)
        decorators = "".join(Decorator(c).render(indentation) for c in decorators)
        head = indent("def %s(%s):" % (self.name, ", ".join(params)), indentation)
        children = self.get_children()
        if not children:
            self.add(Stmt("pass"))
        body = "".join(c.render(indentation+1) for c in children)
        return "%s%s\n%s" % (decorators, head, body)


class ClassMethod(Function):

    def __init__(self, *args, **kwargs):
        super(ClassMethod, self).__init__(*args, **kwargs)
        self.method = "class"


class StaticMethod(Function):

    def __init__(self, *args, **kwargs):
        super(StaticMethod, self).__init__(*args, **kwargs)
        self.method = "static"


class Method(Function):

    def __init__(self, *args, **kwargs):
        super(Method, self).__init__(*args, **kwargs)
        self.method = "instance"


class Class(Block):

    def __init__(self, name, bases=None, decorators=None):
        super(Class, self).__init__(name)
        self.bases = bases or ["object"]
        self.decorators = decorators or []

    def add(self, code):
        super(Class, self).add(code)
        if isinstance(code, Function) and not code.method:
            code.method = "instance"

    def render(self, indentation=0):
        children = self.get_children()
        head = indent("class %s(%s):" % (self.name, ", ".join(self.bases)), indentation)
        content = "\n".join(c.render(indentation+1) for c in children)
        decorators = "".join(Decorator(d).render(indentation) for d in self.decorators)
        return "%s%s\n\n%s" % (decorators, head, content)


class Module(Block):

    def __init__(self, module):
        self.code_obj = module
        super(Module, self).__init__(module.__name__)
        self.imports = []

    def export(self, *args, **kwargs):
        return self.imports.append((args, kwargs))

    @property
    def code(self):
        return self.code_obj

    def render(self):
        indentation = 0
        children = self.get_children()
        content = "\n\n".join(c.render(indentation+1) for c in children)
        return content


if __name__ == '__main__':
    import sample
    func = Function("any", ["a", "b", "c"], varargs="args", varkw="kwargs", defaults={"a": 90}, decorators=["aaa", "bbb"])
    cl = Class("TestModel1", ["Any", "Another"], decorators=["jhjkh"])
    cl.add(func)
    cl.add(Method("get_queryset", varkw="kwargs"))
    cl.add(Assign("another", "5"))
    mod = Module(sample)
    mod.add(cl)

    print(mod.render())
