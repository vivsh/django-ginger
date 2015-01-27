
import os
from django.core.management import BaseCommand
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        base_dir = os.path.join(os.environ['VIRTUAL_ENV'], "../")
        content = template.format(project_dir=base_dir.rstrip("/") + "/",
                                  project_name=settings.PROJECT_NAME,
                                  project_port=settings.PROJECT_PORT)
        self.stdout.write(content)



template = """
[uwsgi]

chdir           = {project_dir}src/

module          = {project_name}.wsgi

home            = {project_dir}venv/

http-socket     = 0.0.0.0:{project_port}

master          = true

pidfile         = {project_dir}run/uwsgi.pid

logto           = {project_dir}log/uwsgi.log

processes       = 2

threads         = 10

vacuum          = true

harakiri-verbose= 1

auto-procname   = 1

no-orphans      = 1

master          = 1

disable-logging = false

limit-post      = 153600000

http-timeout    = 10

threads         = 10

enable-threads  = 1

touch-reload    = {project_dir}src/etc/uwsgi.ini
"""
