
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
        output = path.join(static_dir, "css", "%s.css" % filename)
        includes = [
            path.join(path.dirname(assets.__file__), "sass"),
            sass_dir
        ]
        binaries = (utils.which("scss"), utils.which("sassc"))
        exe = filter(None, binaries)[0]
        sassc = binaries[0] == exe

        cmd = [exe]
        if options["watch"]:
            cmd.append("--watch")
        for inc in includes:
            cmd.append("-I%s" % inc)

        if sassc:
            cmd.extend((source, output))
        else:
            cmd.append("%s:%s" % (source, output))
        print(cmd)
        try:
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as ex:
            self.stderr.write(ex.output)
        else:
            self.stdout.write(output)


