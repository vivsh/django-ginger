
import os
from django.core.management import BaseCommand
from django.conf import settings


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-n","--name", type=str, dest="name", help="Name of the project. "
                                                      "This should be same as the basename for the .wsgi file",
                            nargs="?")
        parser.add_argument("-p", "--port", dest="port", type=int, help="Project port")

    def handle(self, **options):
        base_dir = os.path.abspath(os.path.join(os.environ['VIRTUAL_ENV'], "../"))
        content = template.format(project_dir=base_dir.rstrip("/") + "/",
                                  project_name=options['name'],
                                  project_port=options['port']
                                  )
        self.stdout.write(content)



template = """
[uwsgi]

chdir           = {project_dir}src/

module          = {project_name}.wsgi

home            = {project_dir}venv/

env = VIRTUAL_ENV={project_dir}venv/

http-socket     = 0.0.0.0:{project_port}

master          = true

pidfile         = {project_dir}run/uwsgi.pid

#logto           = {project_dir}log/uwsgi.log

processes       = 2

enable-threads  = 1

threads         = 10

vacuum          = true

harakiri-verbose= 1

auto-procname   = 1

no-orphans      = 1

master          = 1

disable-logging = false

limit-post      = 153600000

http-timeout    = 10

touch-reload    = {project_dir}src/uwsgi.ini
"""
