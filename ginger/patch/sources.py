
import os
from os import path
import ast
from .utils import get_indentation, set_indentation


class FileSource(object):

    def __init__(self, filename, tabwidth=4):
        self.filename = filename
        content = open(self.filename).read().rstrip() + os.linesep
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
        return get_indentation(line, tabwidth)

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

    def check_closed(self):
        if not self.valid:
            raise ValueError("Cannot insert in a closed file")

    def remove(self, index):
        self.lines.pop(index)

    def replace(self, index, line):
        self.check_closed()
        self.lines.pop(index)
        self.lines.insert(index, line)

    def insert(self, index, line):
        self.check_closed()
        self.lines.insert(index, line)

    def save(self):
        self.check_closed()
        with open(self.filename, "w") as fh:
            fh.writelines(self.lines)


class SymbolSource(object):
    name = None
    parent = None
    header_span = 1

    span = ()

    def __init__(self, node, source):
        super(SymbolSource, self).__init__()
        self.symbols = []
        self.parse(node, source)

    def is_first_child(self, name):
        return self.symbols and self.symbols[0].name == name

    @property
    def is_first(self):
        return self.parent.symbols[0] is self

    def remove_pass(self):
        exists = False
        for sym in self.symbols:
            if isinstance(sym.node, ast.Pass):
                first, last = sym.span
                self.source.remove(first-1)
                exists = True
        if exists:
            self.save()

    def indentation(self, tabwidth=4):
        first, last = self.span
        return get_indentation(self.source[first-1], tabwidth=tabwidth)

    def child_indentation(self, tabwidth=4):
        return self.symbols[0].indentation(tabwidth) if self.symbols else self.indentation(tabwidth)+tabwidth

    def find_all(self, name):
        if not name:
            yield self
        else:
            name, tail = name.split(".", 1) if "." in name else (name, "")
            for cl in reversed(self.symbols):
                if cl.name == name:
                    for val in cl.find_all(tail):
                        yield val

    def format_code(self, code, is_child, tabwidth=4, gap=0):
        if hasattr(code, 'render'):
            if is_child:
                padding = self.child_indentation(tabwidth)
            else:
                padding = self.indentation(tabwidth)
            code = code.render(padding)
        code = "%s%s" % (gap*os.linesep, code)
        return code

    def insert(self, index, code, is_child, gap=0):
        code = self.format_code(code, is_child, tabwidth=4, gap=gap)
        first, last = self.span
        self.source.insert(index+first-1, code)
        self.save()

    def find_position(self, index):
        first, last = self.span
        return index+first-1

    def find_line(self,index):
        return self.source[self.find_position(index)]

    def replace(self, index, code, is_child, gap=0):
        code = self.format_code(code, is_child, tabwidth=4, gap=gap)
        self.source.replace(self.find_position(index), code)
        self.save()

    def remove(self, index):
        self.source.remove(self.find_position(index))
        self.save()

    def prepend(self, code, gap=0):
        self.insert(self.header_span, code, is_child=True, gap=gap)

    def append(self, code, gap=0):
        self.insert(self.span[1]+1-self.span[0], code, is_child=True, gap=gap)

    def add_child(self, code, gap=0):
        self.append(code, gap=gap)

    def save(self):
        if self.parent:
            self.parent.save()
        else:
            self.source.save()

    @property
    def total_lines(self):
        first, last = self.span
        return last - first

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

    def parse(self, node, source):
        self.source = source
        self.node = node
        self.name = getattr(node, 'name', None)
        self.parse_position()
        self.parse_children()

    def parse_position(self):
        node = self.node
        first = node.lineno
        last = first
        for n in ast.walk(self.node):
            if hasattr(n, "lineno"):
                if n.lineno > last:
                    last = n.lineno
        self.span = (first, last)

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
                result = SymbolSource(child, self.source)
            symbols.append(result)
            result.parent = self
        self.symbols = symbols

    def make_symbol(self, class_, child):
        name = getattr(child, "name", None)
        for sym in self.symbols[:]:
            if class_ in (ClassSource, FunctionSource) and isinstance(sym, class_) and sym.name == name:
                sym.parse(child, self.source)
                return sym
        return class_(child, self.source)

    def handle_classdef(self, child):
        return self.make_symbol(ClassSource, child)

    def handle_functiondef(self, node):
        return self.make_symbol(FunctionSource, node)


class BlockSourceMixin(object):

    @property
    def decorators(self):
        return tuple(a.id for a in self.node.decorator_list)

    def format_header(self, line):
        padding = " " * self.indentation()
        header = "%s%s\n" % (padding, line.strip())
        return header

    def set_signature(self, header):
        header = self.format_header(header)
        pos = len(self.decorators)
        line = self.find_line(pos)
        if not line.strip():
            raise TypeError("There cannot be a gap between decorators and signature")
        self.replace(pos, header, is_child=False, gap=0)

    def set_decorators(self, decorators):
        ind = self.indentation()
        for dec in decorators:
            name = getattr(dec, "name", dec)
            code = dec.render(ind) if hasattr(dec, "render") else "@%s" % dec
            if name not in self.decorators:
                dec = self.format_header(code)
                self.add_decorator(dec)

    def add_decorator(self, code, position=0):
        total = len(self.decorators)
        if total == 0:
            position = 0
        if position >= total:
            position = total
        if position < 0:
            position %= total
        if position < 0:
            position += total
        self.insert(position, code, is_child=False)

    def is_empty(self):
        return not self.symbols or all(isinstance(s.node, ast.Pass) for s in self.symbols)

    def has_pass(self):
        return any(isinstance(s.node, ast.Pass) for s in self.symbols)


class FunctionSource(BlockSourceMixin, SymbolSource):


    def parse_children(self):
        return

    def set_signature(self, header):
        raise NotImplementedError


class ClassSource(BlockSourceMixin, SymbolSource):

    decorators = ()
    bases = ()

    @property
    def bases(self):
        return tuple(a.id for a in self.node.bases)


class ModuleSource(SymbolSource):

    header_span = 0

    def __init__(self, filename):
        self.set_filename(filename)
        super(ModuleSource, self).__init__(self.node, self.source)

    def set_filename(self, filename):
        self.filename = filename
        self.source = FileSource(self.filename)
        self.node = ast.parse(self.source.content)

    def indentation(self, tabwidth=4):
        if self.symbols:
            return self.symbols[0].indentation()
        else:
            return 0

    def child_indentation(self, tabwidth=4):
        return self.indentation(tabwidth)

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
        super(ModuleSource, self).parse(*args, **kwargs)
        self.revise_end(len(self.source))


def find(filename, name):
    base_name = path.splitext(path.basename(filename))[0]
    parts = name.split(".", 1)
    if not parts or base_name != parts.pop(0):
        raise ValueError("Filename does not belong to this module: %s" % filename)
    name = ".".join(parts)
    return ModuleSource(filename).find(name)
