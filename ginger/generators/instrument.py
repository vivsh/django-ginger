
from os import path
import inspect
import ast
import itertools
import astunparse

"""
Add/remove class methods/properties
Preserve comment
"""


def find_indentation(line, tabwidth=4):
    return sum(tabwidth if i == '\t' else 1
                for i in (itertools.takewhile(lambda c: c.isspace(), (c for c in line))))


class Source(object):

    def __init__(self, filename, tabwidth=4):
        self.filename = path.abspath(filename)
        content = open(self.filename).read()
        self.lines = content.splitlines(True)
        self.tabwidth = tabwidth
        self.valid = True

    def close(self):
        self.valid = False

    @property
    def content(self):
        return "".join(self.lines)

    def indentation(self, line):
        tabwidth = self.tabwidth
        if isinstance(line, int):
            line = self.lines[line]
        return find_indentation(line, tabwidth)

    def indent(self, line, width):
        total = self.indentation(line)
        content = line[total: ]
        return " "*width + content

    def __len__(self):
        return len(self.lines)

    def __iter__(self):
        return iter(self.lines)

    def __getitem__(self, item):
        return self.lines.__getitem__(item)

    def __setitem__(self, key, line):
        if isinstance(key, slice):
            lines = line
            start, end, step = slice
            del self.lines[start:end:step]
            for i, ln in enumerate(lines):
                self.insert(start+i, ln)
        else:
            self.insert(key, line)

    def insert(self, index, line):
        if not self.valid:
            raise ValueError("Cannot insert in a closed file")
        self.lines.insert(index, line)

    def save(self):
        if not self.valid:
            raise ValueError("Cannot save to a closed file")
        with open(self.filename, "w") as fh:
            fh.writelines(self.lines)


class Symbol(object):
    name = None
    parent = None
    span = ()

    def __init__(self, node, source):
        super(Symbol, self).__init__()
        self.symbols = []
        self.parse(node, source)

    @property
    def indentation(self):
        first, last = self.span
        return find_indentation(self.source[first-1])

    def find_all(self, name):
        if not name:
            yield self
        else:
            name, tail = name.split(".", 1) if "." in name else (name, "")
            for cl in reversed(self.symbols):
                if cl.name == name:
                    for val in cl.find_all(tail):
                        yield val

    def insert(self, index, code):
        if hasattr(code, 'render'):
            code = code.render(self.indentation)
        first, last = self.span
        self.source.insert(index+first-1, code)
        self.save()

    def save(self):
        if self.parent:
            self.parent.save()
        else:
            self.source.save()

    def find(self, name):
        return next(self.find_all(name), None)

    def __contains__(self, name):
        return self.find(name) is not None

    def revise_end(self, lineno):
        """

        :param lineno: line number of the line above the next sibling node
        :return:
        """
        span = self.span
        if lineno > span[-1]:
            last = lineno
            lines = self.source
            limit = len(self.source)
            while limit > last-1 and not lines[last-1].strip():
                last -= 1
            self.span = self.span[0], last
        else:
            last = self.span[-1]
        for sym in reversed(self.symbols):
            sym.revise_end(last)
            last = sym.span[0]-1
        # print("Span for %s is %r"%(self, self.span))


    def parse_position(self):
        node  = self.node
        first = node.lineno
        last = first
        for n in ast.walk(self.node):
            if hasattr(n, "lineno"):
                if n.lineno > last:
                    last = n.lineno
        self.span = (first, last)

    def parse(self, node, source):
        self.source = source
        self.node = node
        self.name = getattr(node, 'name', None)
        self.parse_position()
        self.parse_children()

    def parse_children(self):
        symbols = []
        for child in ast.iter_child_nodes(self.node):
            if not isinstance(child, ast.stmt):
                continue
            result = None
            class_name = child.__class__.__name__.lower()
            method = "handle_%s" % class_name
            func = getattr(self, method, None)
            if func:
                result = func(child)
            if not result:
                # if isinstance(child, ast.Assign):
                # print(child)
                result = Symbol(child, self.source)
            symbols.append(result)
            result.parent = self
        self.symbols = symbols

    def make_symbol(self, class_, child):
        name = getattr(child, "name", None)
        for sym in self.symbols[:]:
            if class_ in (Class, Function) and isinstance(sym, class_) and sym.name == name:
                sym.parse(child, self.source)
                return sym
        return class_(child, self.source)

    def handle_classdef(self, child):
        return self.make_symbol(Class, child)

    def handle_functiondef(self, node):
        return self.make_symbol(Function, node)

    def handle_import(self, node):
        return Import(node, self.source)

    def handle_importfrom(self, node):
        return ImportFrom(node, self.source)


class Expr(Symbol):
    pass


class Assign(Symbol):
    pass


class ImportFrom(Symbol):
    pass


class Import(Symbol):
    pass


class Assign(object):
    pass


class Function(Symbol):

    def parse_children(self):
        return



class Class(Symbol):
    pass



class Module(Symbol):

    def __init__(self, filename):
        self.set_filename(filename)
        super(Module, self).__init__(self.node, self.source)

    def set_filename(self, filename):
        self.filename = filename
        self.source = Source(self.filename)
        self.node = ast.parse(self.source.content)

    def reload(self):
        self.set_filename(self.filename)
        self.parse(self.node, self.source)

    def save(self):
        self.source.save()
        self.source.close()
        self.reload()

    def parse_position(self):
        self.span = (1, len(self.source))

    def parse(self, *args, **kwargs):
        super(Module, self).parse(*args, **kwargs)
        self.revise_end(len(self.source))


def get_source_span(filename, name=""):
    mod = Module(filename)
    result = mod.find(name)
    return result.span, result.indentation

if __name__ == '__main__':
    filename = "sample.py"
    mod = Module(filename)
    cl = mod.find("TestModel")
    mod.insert(0, "import something")



