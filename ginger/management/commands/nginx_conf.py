
from django.conf import settings
from django.core.management import BaseCommand, CommandError
from os import path

template = """
upstream django {
        # connect to this socket
        # server unix:///tmp/uwsgi.sock;    # for a file socket
        server 127.0.0.1:%(uwsgi_port)s;      # for a web port socket
}

server {
    # the port your site will be served on
    listen      %(site_port)s;
    # the domain name it will serve for
    server_name %(site_name)s;   # substitute your machine's IP address or FQDN
    charset     utf-8;

    #Max upload size
    client_max_body_size 75M;   # adjust to taste

    # Django media
    location /media  {
        alias %(media_root)s;      # your Django project's media files
    }

    location /static {
            alias %(static_root)s;     # your Django project's static files
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /etc/nginx/uwsgi_params; # or the uwsgi_params you installed manually
    }
}
"""

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-u", "--uwsgi-port", type=int, help="Port that'll run with uwsgi")
        parser.add_argument("-p", "--site-port", type=int, help="Server port.", default=80)
        parser.add_argument("-n", "--site-name", type=str, help="Server name that'll be used inside nginx conf",
                            nargs='?')

    def handle(self, *args, **options):
        ip_list = settings.ALLOWED_HOSTS
        context = {
            "media_root": settings.MEDIA_ROOT,
            "static_root": settings.STATIC_ROOT,
            "site_name": options.get('site_name', ip_list[0] if ip_list else "127.0.0.1"),
            "site_port": options.get('site_port', 80),
            "uwsgi_port": options['uwsgi_port']
        }
        self.stdout.write(template % context)
        self.stdout.write("\n\n")
