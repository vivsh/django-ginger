

import itertools


def get_indentation(line, tabwidth=4):
    return sum(tabwidth if i == '\t' else 1
                for i in (itertools.takewhile(lambda c: c.isspace(), (c for c in line))))


def set_indentation(line, width):
    return "%s%s" % (" "*width, line)

def builtins():
    try:
        from django.utils import six
    except ImportError as ex:
        import six
    return six.moves.builtins
    # try:
    #     import __builtin__
    #     return __builtin__
    # except ImportError:
    #     import builtins
    #     return builtins


def clean_lines(content):
    indentation = 0
    first = True
    for ln in content.splitlines():
        if first and not ln.strip():
            continue
        if first:
            first = False
            indentation = sum(1 for _ in itertools.takewhile(lambda c: c.isspace(), ln))
        ln = ln[indentation:]
        yield ln

