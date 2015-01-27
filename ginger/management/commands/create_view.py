
import optparse
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from ginger.generators import views


class Command(BaseCommand):
    view_types = ['new','detail', 'edit', 'search', 'list', 'form', 'form-done', 'wizard', 'template']

    help = "Creates a view and its associated forms/templates. " \
           "If any class already exists then it will never be over-written."

    option_list = BaseCommand.option_list + (
        optparse.make_option("-m", "--model",
                             action="store",
                             help="Model associated with the view"),
        optparse.make_option("-t", "--type",
                             action="store",
                             type="choice",
                             choices=view_types,
                             help="type of view: %s" % ", ".join(view_types)),
    )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No view has been given")
        if len(args) > 1:
            raise CommandError("Too many arguments. Check python manage.py help create_view")
        view = args[0]
        app_name, resource = view.split(".", 1)
        app = views.Application(app_name, resource, options["model"])
        app.generate_view(resource, options["type"])


