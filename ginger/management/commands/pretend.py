
import pprint
from optparse import make_option
from django.apps import apps
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

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No model specified")
        name = args[0]
        if len(args) > 1 :
            raise CommandError("Too many arguments")
        app_label, model_name = name.split(".", 1)
        model = apps.get_model(app_label, model_name)
        pretense = options["pretense"]
        verbose = int(options["verbosity"]) > 1
        callback = self.verbose if verbose else None
        pretenses.generate(model, options['total'], name=pretense, callback=callback)

    def verbose(self, data):
        self.stdout.write(pprint.pformat(data, indent=4))
        self.stdout.write("\n")