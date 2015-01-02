
import optparse
from django.core.management import BaseCommand
from ginger.generators import views


class Command(BaseCommand):

    help = "Creates a view and its associated forms/templates"

    option_list = BaseCommand.option_list + (
        optparse.make_option("-m", "--model",
                             action="store",
                             help="Model associated with the view"),
        optparse.make_option("-t", "--type",
                             action="store",
                             help="type of view: new detail, edit, delete, search, list, form"),
    )

    def handle(self, view, **options):
        app_name, resource = view.split(".", 1)
        app = views.Application(app_name, resource, options["model"])
        app.generate_view(resource, options["type"])


