
from optparse import make_option
from django.apps import apps
from ginger.pretenses import Factory
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):

    args = "app_name.model_name"
    help = 'Create data for the specified model'

    option_list = BaseCommand.option_list + (
        make_option(
            "--total",
            default=20,
            type="int",
            help="Total number of instances to be created"
        ),
    )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No model specified")
        name = args[0]
        if len(args) > 1 :
            raise CommandError("Too many arguments")
        app_label, model_name = name.split(".", 1)
        model = apps.get_model(app_label, model_name)
        fac = Factory(model, options["total"])
        fac.create_all()