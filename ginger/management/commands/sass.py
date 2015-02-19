
from os import path
import optparse
import subprocess
from django.apps import apps
from django.contrib.staticfiles import finders
from django.core.management import BaseCommand, CommandError
from ginger import assets, utils


class Command(BaseCommand):
    args = "input-file [output-file]"

    help = "Compile sass files"
    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "-w",
            "--watch",
            action="store_true",
            default=False
        ),
    )
    def handle(self, input="scss/main.scss", output=None, **options):
        if path.exists(input):
            source = input
        else:
            source = finders.find(input)
        if not path.exists(source):
            raise CommandError("Input file does not exist: %s" % source)
        sass_dir = path.dirname(source)
        static_dir = path.dirname(sass_dir)
        filename, _ = path.splitext(path.basename(source))
        output = path.join(static_dir, "css", "%s_.css" % filename)
        includes = [
            path.join(path.dirname(assets.__file__), "sass"),
            sass_dir
        ]
        binaries = (utils.which("sassc"), utils.which("scss"))
        exe = next((b for b in binaries if b is not None), None)
        cmd = [exe]
        if options["watch"]:
            cmd.append("-w")
        for inc in includes:
            cmd.append("-I%s" % inc)
        cmd.append(source)
        cmd.append(output)
        try:
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as ex:
            self.stderr.write(ex.output)
        else:
            self.stdout.write(output)


