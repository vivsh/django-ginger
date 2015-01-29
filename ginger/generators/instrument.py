
from os import path
import ast
import itertools
import astunparse

"""
Add/remove class methods/properties
Preserve comment
"""

class Source(object):

    def __init__(self, filename, tabwidth=4):
        self.filename = path.abspath(filename)
        content = open(self.filename).read()
        self.lines = content.splitlines(True)
        self.tabwidth = tabwidth

    @property
    def content(self):
        return "".join(self.lines)

    def indentation(self, line):
        tabwidth = self.tabwidth
        if isinstance(line, int):
            line = self.lines[line]
        return sum(tabwidth if i == '\t' else 1
                   for i in (itertools.takewhile(lambda c: c.isspace(), (c for c in line))))

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

    def _check_line(self, index, line):
        if line.endswith("\n"):
            raise ValueError("Line should be terminated with a \\n at %d" % index)

    def append(self, line):
        self.lines.append(line)

    def extend(self, lines):
        for line in lines:
            self.append(line)

    def insert(self, index, line):
        self._check_line(index, line)
        self.lines.insert(index, line)

    def save(self):
        with open(self.filename, "w") as fh:
            fh.writelines(self.lines)


class Symbol(object):
    name = None
    span = ()

    def __init__(self, node, source):
        self.source = source
        self.node = node
        self.symbols = []
        self.parse()

    def find_all(self, class_):
        for cl in self.symbols:
            if isinstance(cl, class_):
                yield cl

    def find(self, class_):
        return next(self.find_all(class_), None)

    def revise_end(self, lineno):
        last = lineno - 1
        lines = self.source
        limit = len(self.source)

        while limit > last-1 and not lines[last-1].strip():
            last -= 1
        self.span = self.span[0], last
        print "Span for %r is (%d, %d)" % (self.__class__, self.span[0], self.span[1])
        for sym in reversed(self.symbols):
            sym.revise_end(last)
            last = sym.span[0]


    def set_position(self, node):
        self.name = getattr(node, 'name', None)
        first = node.lineno
        last = first
        for n in ast.walk(self.node):
            if hasattr(n, "lineno"):
                if n.lineno > last:
                    last = n.lineno
        self.span = (first, last)

    def parse(self):
        self.set_position(self.node)
        for child in ast.iter_child_nodes(self.node):
            if not isinstance(child, ast.stmt):
                continue
            result = None
            class_name = child.__class__.__name__.lower()
            method = "handle_%s"%class_name
            func = getattr(self, method, None)
            if func:
                result = func(child)
            if not result:
                if isinstance(child, ast.Assign):
                    print(child)
                result = Symbol(child, self.source)
            self.symbols.append(result)


    def handle_classdef(self, child):
        return Class(child, self.source)

    def handle_functiondef(self, node):
        return Function(node, self.source)

    def handle_import(self, node):
        return Import(node, self.source)

    def handle_importfrom(self, node):
        return ImportFrom(node, self.source)


class ImportFrom(Symbol):

    def get_position(self, node):
        super(ImportFrom, self).get_position(node)
        first, last = self.span
        print self.source[last-1], "<<<<<<<"


class Import(Symbol):
    pass


class Assign(object):
    pass


class Function(Symbol):
    pass


class Class(Symbol):
    pass



class Module(Symbol):

    def __init__(self, filename):
        self.filename = filename
        source = open(self.filename).read()
        node = ast.parse(source)
        super(Module, self).__init__(node, source.splitlines(True))

    def set_position(self, node):
        self.span = (1, len(self.source))
        return

    def parse(self):
        super(Module, self).parse()
        self.revise_end(len(self.source)-1)


if __name__ == '__main__':
    filename = path.abspath("sample.py")
    mod = Module(filename)
    class_ = mod.find(Class)
    print class_.name, class_.span



