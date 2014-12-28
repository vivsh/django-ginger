
import os
import ast
import inspect
# from django.core.management import BaseCommand


def get_identifiers(filename):
    source = open(filename).read()
    tree = ast.parse(source)
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, ast.Assign):
            for n in child.targets:
                if isinstance(n, ast.Name):
                    yield n.id, child.lineno, child.col_offset
                else:
                    for a in ast.walk(n):
                        if isinstance(a, ast.Name):
                            yield a.id, child.lineno, child.col_offset
        if not isinstance(child, (ast.FunctionDef, ast.ClassDef)):
            continue
        name = child.name
        line = child.lineno
        col = child.col_offset
        yield name, line, col


def check_name(name, filename):
    if not os.path.exists(filename):
        return False
    for identifier, line, offset in get_identifiers(filename):
        if name == identifier:
            raise ValueError("%r is already defined in line %s of %s" % (name, line, filename))


def list_view(resource):
    template_folder()
    include_folder()
    check_file()
    check_file()
    check_base()

def create_detail_view():
    pass

def create_delete_view():
    pass

def create_edit_view():
    pass

def create_form():
    pass


# class Command(BaseCommand):
#
#     def handle(self, *args, **options):
#         pass

class Anything(object):
    pass


if __name__ == '__main__':
    import __main__ as current_module
    check_name("copything", inspect.getsourcefile(current_module))