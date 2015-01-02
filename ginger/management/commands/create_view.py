
import optparse
from django.core.management import BaseCommand
from ginger.generators import views


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        optparse.make_option("-m", "--model",
                             action="store",
                             help="Model associated with the view"),
    )

    @staticmethod
    def get_model(app, resource, model):
        if model is None:
            model = resource
        try:
            return app.get_model(model)
        except LookupError:
            return None

    def handle(self, view, *kinds, **options):
        app_name, resource = view.split(".", 1)
        app = views.Application(app_name, resource, options["model"])
        model = self.get_model(app.app, resource, options['model'])
        kinds = tuple(filter(lambda a: bool(a), (k.strip(" ,-:").lower() for k in kinds)))
        app.generate_view(resource)


