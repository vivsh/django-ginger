import os
import re
import hashlib
import subprocess
import importlib
import inspect
import optparse

from django.core.management import BaseCommand, CommandError, call_command
from django.conf import settings
from django.contrib.staticfiles import finders, storage
from django.template import loader
from django.template.base import TemplateDoesNotExist

def project_path():
    attrs = ["BASE_DIR", "PROJECT_DIR", "PROJECT_ROOT"]
    try:
        return next(getattr(settings,attr) for attr in attrs if hasattr(settings, attr))
    except StopIteration:
        pass
    try:
        module = importlib.import_module(project_name())
        result = os.path.realpath(os.path.dirname(inspect.getsourcefile(module)))
        return result
    except ImportError:
        pass
    raise ValueError("Failed to find the base dir for this project")

def project_name():
    return settings.ROOT_URLCONF.split(".", 1)[0]    

def local(cmd):
    return subprocess.check_call(cmd, cwd=project_path(), shell=True)

def asset(path, *tail):
    abspath = os.path.join(settings.STATIC_ROOT, path)
    if os.path.exists(abspath):
        return os.path.join(abspath, *tail)
    else:
        return None

def find_asset(path, *tail):
    assets_folder = finders.find(path)
    return os.path.join(assets_folder, *tail)

def template(name):
    from django.template import engines
    for nm in engines:
        engine = engines[nm]
        try:
            return next(filename for filename in engine.iter_template_filenames(name) if os.path.exists(filename))
        except StopIteration:
            pass
    path = os.path.join(project_path(), project_name(), "templates", "requirejs.html")
    with open(path, "w") as fh:
        fh.write("")
    return path
    

def file_size(filename):
    size = os.path.getsize(filename)
    
    gb = size/(1024*1024*1024.0)
    if gb > 1: 
        return "%.2f gb"%gb
    
    gb = size/(1024*1024.0)
    if gb > 1: 
        return "%.2f mb"%gb
    
    gb = size/1024.0
    if gb > 1: 
        return "%.2f kb"%gb
    
    return "%d bytes"%size

    
def change_version(filename, repl):
    if os.path.isfile(filename) and os.access(filename, os.R_OK):      
        content = open(filename).read()
    else:
        content = ""
    if callable(repl):
        content = repl(content)
    else: 
        content = repl
    with open(filename,"w") as fh:
        fh.write(content)     
        
    
def remove_files(base_dir, pattern, recursive=False):
    pattern = re.compile(pattern)
    cdir = os.getcwd()
    base_dir = os.path.realpath(os.path.join(cdir,base_dir))
    if recursive:
        sources = os.walk(base_dir)
    else:
        sources = ( (base_dir, [], [f]) for f in os.listdir(base_dir) ) 
    for root, _, files in sources:
        for f in files:
            filename = os.path.join(root, f)
            if pattern.findall(filename):
                os.unlink(filename)
            
def hashdir(dirname, ext="js"):
    hasher = hashlib.sha1()
    for root, _, files in os.walk(dirname):
        for f in files:
            if f.endswith(".min.%s"%ext) :
                continue
            filename = os.path.join(root, f)
            blocksize = 64 *1024
            afile = open(filename, "rb")
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)
    return "%s.min.%s"%(hasher.hexdigest()[:16], ext)

def get_requirejs_path():
    default_path = "bower_components/requirejs/require.js"
    requirejs_path = getattr(settings, "REQUIREJS_PATH", default_path)
    if not find_asset(requirejs_path):
        raise AttributeError("No REQUIREJS_PATH has been specified in settings")
    return requirejs_path


def pack_js(main, optimize):
    call_command("collectstatic", interactive=False, verbosity=0)
    root = asset("js")
    hashjs = hashdir(root,"js")
    outfile = find_asset("js", hashjs)
    
    requirejs_path = get_requirejs_path()
    
    change_version(template('requirejs.html'), "<script src='{{STATIC_URL}}js/%s' type='text/javascript'></script>"%(hashjs,))
    
    if os.path.exists(outfile):
        print("No change detected")
        return
 
    remove_files(find_asset("js"), r".{16}\.min\.js$")
    require_module = asset(requirejs_path)[:-3]
       
    options = {
        "baseUrl": asset("js"),
        "name": "main",
        "out": outfile,
        "mainConfigFile": asset("js/%s" % main),
        "optimize": optimize,
        "preserveLicenseComments":"false",
        "paths.requireLib": require_module,
        "include":"requireLib"
    } 
    
    optargs = " ".join("%s=%s"%(k,v)  for k,v in options.iteritems())
    local("r.js -o %s"%optargs)
    
    print("Output: %s %s"%(outfile, file_size(outfile)))


def unpack_js():
    change_version(template('requirejs.html'), "<script src='{{STATIC_URL}}%s' data-main='{{STATIC_URL}}js/main' type='text/javascript'></script>"%(get_requirejs_path()))


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-u",
            "--unpack",
            action="store_true",
            default=False)
        parser.add_argument(
            "-m",
            "--main",
            default="main.js"
        )
        parser.add_argument(
            "-o",
            "--optimize",
            type=str,
            choices=("none", "uglify", "uglify2"),
            default="none",
        )

    def handle(self, **options):
        main_file = options["main"]
        unpack = options["unpack"]
        optimize = options["optimize"]
        if unpack:
            unpack_js()
        else:
            pack_js(main_file, optimize)