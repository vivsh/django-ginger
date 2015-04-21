
import pprint
from optparse import make_option
from django.apps import apps
from django.conf import settings
from ginger import pretenses
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):

    option_list = (

    ) + BaseCommand.option_list

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("This command cannot be run in production environment")
        if len(args) == 1 and "." in args[0]:
            name = args[0]
            app_label, model_name = name.split(".", 1)
            model = apps.get_model(app_label, model_name)
            self.truncate_model(model)
        elif not args:
            for app in apps.get_app_configs():
                self.truncate_app(app)
        else:
            for name in args:
                app = apps.get_app_config(name)
                self.truncate_app(app)

    def truncate_app(self, app):
        models = app.get_models()
        map(self.truncate_model, models)

    def truncate_model(self, model):
        model.objects.all().delete()
