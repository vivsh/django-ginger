

from django.apps import apps
from django.core.management import BaseCommand, CommandError



class Command(BaseCommand):
    args = "app_name"

    help = "Converts any app to standard ginger app with celery-tasks, forms, signals modules"

    def handle(self, *args, **options):
        app_configs = apps.get_app_configs()


