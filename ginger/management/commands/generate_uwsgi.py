
import os
import importlib
import inspect

from django.core.management import BaseCommand
from django.conf import settings

def project_path():
    attrs = ["PROJECT_PATH_", "BASE_DIR", "PROJECT_DIR", "PROJECT_ROOT"]
    try:
        return next(getattr(settings,attr) for attr in attrs if hasattr(settings, attr))
    except StopIteration:
        pass
    try:
        module = importlib.import_module(project_name())
        result = os.path.realpath(os.path.dirname(inspect.getsourcefile(module)))
        return result
    except ImportError:
        pass
    raise ValueError("Failed to find the base dir for this project")

def project_name():
    return settings.ROOT_URLCONF.split(".", 1)[0]    

class Command(BaseCommand):
    
    def handle(self, mode, target="all", **options):
        pass
