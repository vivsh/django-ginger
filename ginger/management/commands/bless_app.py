
import optparse
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from ginger.generators import views


class Command(BaseCommand):
    args = "app_name"

    help = "Converts any app to standard ginger app with celery-tasks, forms, signals modules"

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No view has been given")
        if len(args) > 1:
            raise CommandError("Too many arguments. Check python manage.py help bless_app")
        app_name = args[0]
        views.GingerApp(app_name)


