
from contextlib import contextmanager
import os
from fabric.api import local, run, env, cd, settings, prefix

BASE_DIR = os.path.realpath(os.path.dirname(__file__))

DEVELOPMENT_PACKAGES = {
    "django_debug_toolbar",
    "devserver",
    "django_extensions"
}

def relative_path(*args):
    return os.path.join(BASE_DIR, *args)


env.hosts = ['vivek2010@web129.webfaction.com', ]


PRODUCTION_DOC_ROOT = "/home/vivek2010/webapps/ecapp/src"


@contextmanager
def server(base_dir, host="erotq.com", user=None, password=None):
    env.host_string = '%s@%s' % (user, host) if user else host
    env.password = password

    env.activate = "source %s" % os.path.join(base_dir, '../venv/bin/activate')
    env.directory = base_dir

    with cd(env.directory):
        with prefix(env.activate):
            yield

def update_server(message=None):
    if message is not None:
        push(message)
    with cd(PRODUCTION_DOC_ROOT):
        run("git pull origin master")
        with settings(warn_only=True), prefix("source ../venv/bin/activate"):
            run("./manage.py collectstatic --noinput")
        run("touch etc/uwsgi.ini")

def ginger(message):
    with cd("~/Projects/django_ginger/"):
        local("git add . --all")
        local("git commit -am '%s'" % message)
        local("git push origin master")
    with cd(PRODUCTION_DOC_ROOT), prefix("source ../venv/bin/activate"):
        run("pip install -U git+https://github.com/vivsh/django-ginger@master#egg=django_ginger --no-deps")
        run("touch etc/uwsgi.ini")


def freeze():
    packages = local("pip freeze", capture=True)
    with open(relative_path("requirements.txt"), "w") as fr, \
            open(relative_path("dev_requirements.txt"), "w") as fd:
        for line in packages.splitlines(True):
            name = line.strip().split("=", 1)[0]
            fh = fd if name in DEVELOPMENT_PACKAGES else fr
            fh.write(line)
    local("git commit -m 'updated requirements' requirements.txt dev_requirements.txt")


def push(message=None):
    local("git add . --all")
    if message:
        with settings(warn_only=True):
            local("git commit -am '%s'" % message)
            freeze()
    local("git push origin master")


def update(branch="master"):
    local("git pull origin %s" % branch)
    with server(BASE_DIR):
        local("pip install -r requirements.txt")
        local("./manage.py migrate")
