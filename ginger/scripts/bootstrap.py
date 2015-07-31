
import os
import sys
import subprocess
import shutil
import contextlib
import json


current_dir = os.path.dirname(__file__)

_base_dir = None


def which(cmd):
    try:
        return shutil.which(cmd)
    except AttributeError:
        import distutils.spawn
        return distutils.spawn.find_executable(cmd)


def base_dir():
    global _base_dir
    if _base_dir is None:
        try:
            _base_dir = os.path.dirname(os.environ["VIRTUAL_ENV"])
        except KeyError:
            print("This command should only be run from inside a virtual environment")
            raise
    return _base_dir


def script_path(*args):
    _dir = os.path.dirname(__file__)
    return os.path.join(_dir, *args)


def make_path(*args):
    return os.path.join(base_dir(), *args)


def make_dir(*args):
    path = make_path(*args)
    try:
        os.makedirs(path)
    except OSError:
        pass
    return path


def make_dirs(*args):
    for d in args:
        make_dir(d)


def make_file(path, content=None):
    with open(path, "w") as fh:
        if content:
            fh.write(content)


def delete_files(*files):
    for f in files:
        path = make_path(f)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)


@contextlib.contextmanager
def cd(*args):
    path = make_path(*args)
    orig = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(orig)


def can_run(cmd):
    try:
        run(cmd)
        return True
    except subprocess.CalledProcessError:
        return False


def run(cmd, **kwargs):
    try:
        return subprocess.check_output(cmd, universal_newlines=True, shell=True, **kwargs)
    except subprocess.CalledProcessError as ex:
        print(ex.output)
        print("Return code: %s" % ex.cmd, ex.returncode)
        raise


class Project(object):

    def __init__(self, path, name):
        self.base_dir = path
        self.name = name
        env = os.environ.copy()
        parts = env.get("PATH", "").split(os.pathsep)
        parts.insert(0, self.path("node_modules/.bin/"))
        env["PATH"] = os.pathsep.join(parts)
        self.env = env

    def echo(self, template, *args, **kwargs):
        stmt = template.format(*args, **kwargs)
        print(stmt)

    def check_installed(self, cmd, error=None, action=None, test=None):
        if (not which(cmd)) if not test else can_run(test):
            self.echo("{0} is not found.", cmd)
            if action:
                if callable(action):
                    action()
                else:
                    self.run(action)
                self.echo("Successfully installed {0}.", cmd)
            else:
                raise Exception(error or "Failed to run: %r" % cmd)

    def npm_install(self, packages, flags="--save-dev"):
        if not isinstance(packages, (list, tuple)):
            packages = [packages]
        for pkg in packages:
            self.echo("Installing %s" % pkg)
            self.run("npm install %s %s" % (pkg, flags))

    def prepare(self):
        self.check_installed("node")
        self.check_installed("npm")
        self.prepare_npm()
        self.check_installed("bower", action=lambda: self.npm_install("bower", "--save"))
        # self.check_installed("gulp", action=lambda: self.npm_install("gulp"))
        # packages = "gulp-ruby-sass,gulp-autoprefixer,gulp-minify-css,gulp-rename".split(",")
        # for pkg in packages:
        #     self.npm_install(pkg)

    def run(self, cmd):
        run(cmd, cwd=self.path(), env=self.env)

    def create(self):
        run("django-admin.py startproject %s src --template %s" % (
            self.name, script_path("templates", "project_templates"))
        )

    def create_app(self, name):
        with cd(self.base_dir):
            run("python manage.py startapp %s %s --template %s -e=bowerrc,py" % (
                    name,
                    self.path(self.name),
                    script_path("templates", "app_templates")
                )
            )

    def path(self, *args):
        return os.path.join(self.base_dir, *args)

    def write_file(self, name, content, kind=None):
        with open(name, "w") as fh:
            if kind == "json":
                content = json.dumps(content, indent=4)
            fh.write(content)

    def prepare_npm(self):
        values = {
          "name": self.name,
          "version": "1.0.0",
          "description": "",
          "main": "index.js",
          "dependencies": {},
          "devDependencies": {},
          "scripts": {
            "test": "echo \"Error: no test specified\" && exit 1"
          },
          "author": "",
          "license": "ISC"
        }
        self.write_file(self.path("package.json"), values, "json")


    def prepare_bower(self):
        assets = self.path(self.name, "assets")
        config_path = self.path(self.name, "assets", "js/config.js")
        self.write_file(config_path, """
            requirejs.config({
                map: {
                  '*': {
                    'underscore': 'lodash'
                  }
                },
                path:{
                    "jquery": "../bower_components/jquery/dist/jquery",
                    "backbone": "../bower_components/backbone/backbone",
                    "lodash": "../bower_components/lodash/lodash",
                    "requireLib": "../bower_components/requirejs/require",
                }
            })
        """)
        values = {
            "cwd": assets,
        }
        self.write_file(".bowerrc", values, "json")

        self.write_file(self.path(assets, "bower.json"),{
          "name": self.name,
          "version": '0.0.0',
          "moduleType": [
            'amd'
          ],
          "private": True,
          "ignore": [
            '**/.*',
            'node_modules',
            'bower_components',
            'test',
            'tests'
          ]
        }, "json")

        with open(self.path(".bowerrc"), "w") as fh:
            fh.write(json.dumps(values))

        self.run("bower install jquery backbone font-awesome lodash requirejs --save")

    def manage(self, cmd):
        with cd(self.path()):
            run("python manage.py %s" % cmd)



def main():
    # delete_files("src", "static", "media", "var", "log", ".env")
    make_dirs("src", "static", "media", "var", "log")
    make_file(".env")

    name = sys.argv[1]

    prj = Project(make_path("src"), name)

    prj.prepare()

    prj.create()
    prj.prepare_bower()
    prj.manage("makemigrations auth")
    prj.manage("migrate")
    prj.run("git init .")
    prj.run("npm install gulp gulp-sass")