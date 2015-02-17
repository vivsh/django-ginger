
import optparse
import inspect
import importlib

from django.core.management import BaseCommand
from django.core.management.base import CommandError
from django.utils.module_loading import import_string
from ginger.views import GingerView, utils
from ginger.meta import views


class Command(BaseCommand):
    view_types = ['new','detail', 'edit', 'search', 'list', 'form', 'form-done', 'wizard', 'template']

    help = "Creates a view and its associated forms/templates. " \
           "If any class already exists then it will never be over-written."

    # option_list = BaseCommand.option_list + (
    #     optparse.make_option("-m", "--model",
    #                          action="store",
    #                          help="Model associated with the view"),
    #     optparse.make_option("-t", "--type",
    #                          action="store",
    #                          type="choice",
    #                          choices=view_types,
    #                          help="type of view: %s" % ", ".join(view_types)),
    # )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No view has been given")
        if len(args) > 1:
            raise CommandError("Too many arguments. Check python manage.py help create_view")
        view = args[0]

        try:
            view_class = importlib.import_module(view)
        except ImportError:
            view_class = import_string(view)

        if inspect.ismodule(view_class):
            view_classes = utils.find_views(view_class)
        else:
            view_classes = [view_class]

        for view in view_classes:
            app = views.ViewPatch(view)
            app.patch()


