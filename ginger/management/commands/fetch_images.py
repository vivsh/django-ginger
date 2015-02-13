from django.conf import settings
import os
import optparse
from ginger.extras.google_images import GoogleImage
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "-s",
            "--size",
            action="store",
            dest="size"
        ),
        optparse.make_option(
            "-f",
            "--file-type",
            type="choice",
            choices=["jpg", "png", "svg"],
            default="jpg"
        ),
        optparse.make_option(
            "-u",
            "--unsafe",
            action="store_true"
        ),
        optparse.make_option(
            "-p",
            "--prefix",
            default="image"
        ),
        optparse.make_option(
            "-c",
            "--count",
            default=10,
            type="int"
        ),
    )

    def handle(self, query, dest=None, *args, **options):
        if dest is None:
            dest = ""
        gi = GoogleImage(dest, options["prefix"])
        results = gi.search(query, options["count"],
                  safe= not options["unsafe"],
                  file_type=options["file_type"])
        verbosity = int(options["verbosity"])
        for img in results:
            msg = "Downloaded %s \n" % img
            if verbosity:
                self.stdout.write(msg)


