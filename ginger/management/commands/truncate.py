
import pprint
from optparse import make_option
from django.apps import apps
from django.conf import settings
from ginger import pretenses
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):

    args = "app_name.model_name"
    help = 'Create data for the specified model'

    option_list = (
        make_option(
            "-t",
            "--total",
            default=20,
            type="int",
            help="Total number of instances to be created"
        ),
        make_option(
            "-p",
            "--pretense",
            default=None,
            help="Pretense to be used for content generation"
        ),
    ) + BaseCommand.option_list

    def truncate_model(self, model):
        model.objects.all().delete()

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No model specified")
        name = args[0]
        if len(args) > 1 :
            raise CommandError("Too many arguments")
        if not settings.DEBUG:
            raise CommandError("This command cannot be run in production environment")
        if "." in name:
            app_label, model_name = name.split(".", 1)
            models = [apps.get_model(app_label, model_name)]
        else:
            app = apps.get_app_config(name)
            models = app.get_models()
        map(self.truncate_model, models)