
import optparse
import importlib
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from ginger import views
from ginger.generators import views as gen

class Command(BaseCommand):
    view_types = ['new','detail', 'edit', 'search', 'list', 'form', 'form-done', 'wizard', 'template']

    help = "Creates a view and its associated forms/templates. " \
           "If any class already exists then it will never be over-written."

    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No view has been given")
        if len(args) > 1:
            raise CommandError("Too many arguments. Check python manage.py help create_view")
        module_name = args[0]
        module = importlib.import_module(module_name)
        self.generate_all_views(module)

    def generate_all_views(self, module):
        module_name = module.__name__
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, views.GingerView) and value.__module__ == module_name:
                meta = value.meta
                view_name = value.__name__
                app_label = meta.app.label
                model = None
                if issubclass(value, views.GingerFormView):
                    form_class = value.form_class
                    meta = getattr(form_class, "Meta", None)
                    if meta:
                        model = "%s.%s" % (app_label, meta.model.__name__,)
                gen.Application(app_label, view_name, model).bless_view(value)



