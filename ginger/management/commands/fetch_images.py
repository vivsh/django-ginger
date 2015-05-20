
from ginger.extras.google_images import GoogleImage
from django.core.management import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("query")
        parser.add_argument("--dest", default=None)
        parser.add_argument(
            "-s",
            "--size",
            action="store",
            dest="size"
        )
        parser.add_argument(
            "-f",
            "--file-type",
            type="choice",
            choices=["jpg", "png", "svg"],
            default="jpg"
        )
        parser.add_argument(
            "-u",
            "--unsafe",
            action="store_true"
        )
        parser.add_argument(
            "-p",
            "--prefix",
            default="image"
        )
        parser.add_argument(
            "-c",
            "--count",
            default=10,
            type="int"
        )
    

    def handle(self, **options):
        query = options['query']
        dest = options["dest"]
        gi = GoogleImage(dest, options["prefix"])
        results = gi.search(query, options["count"],
                  safe= not options["unsafe"],
                  file_type=options["file_type"])
        verbosity = int(options["verbosity"])
        for img in results:
            msg = "Downloaded %s \n" % img
            if verbosity:
                self.stdout.write(msg)


