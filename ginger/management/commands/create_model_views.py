
import optparse
from django.core.management import BaseCommand
from ginger.generators import views


class Command(BaseCommand):

    help = "Creates a views associated a model"

    option_list = BaseCommand.option_list + (
        optparse.make_option("-m", "--model",
                             action="store",
                             help="Model associated with the view"),
        optparse.make_option("-t", "--types",
                             default=[],
                             action="append",
                             help="types of view: new detail, edit, delete, search, list, form"),
    )

    def handle(self, view, *args, **options):
        app_name, resource = view.split(".", 1)
        app = views.Application(app_name, resource, options["model"])
        kinds = options["types"] + list(args)
        kinds = tuple(filter(lambda a: bool(a), (k.strip(", ") for k in kinds if k)))
        app.generate_model_views(kinds)


