
from django.apps import apps
from ginger.pretenses import Factory
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):

    args = "app_name.model_name"

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No model specified")
        name = args[0]
        if len(args) > 1 :
            raise CommandError("Too many arguments")
        app_label, model_name = name.split(".", 1)
        model = apps.get_model(app_label, model_name)
        fac = Factory(model, 20)
        fac.create_all()