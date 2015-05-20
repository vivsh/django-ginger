
import optparse
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from ginger.meta import app


class Command(BaseCommand):
    args = "app_name"

    help = "Converts any app to standard ginger app with celery-tasks, forms, signals modules"

    def add_arguments(self, parser):
        parser.add_argument("app_name")

    def handle(self, **options):
        app_name = options["app_name"]
        app.Application(app_name)



