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
    try:
        if loader.template_source_loaders is None:
            loader.find_template(name)
        for l in loader.template_source_loaders:
            for filepath in l.get_template_sources(name):
                if os.access(filepath, os.R_OK):
                    return filepath
    except TemplateDoesNotExist:
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

def get_lesscss_path():
    lesscss_path = getattr(settings, "LESSCSS_PATH", "js/less.js")
    if not asset(lesscss_path):
        raise AttributeError("No LESSCSS_PATH has been specified in settings")
    return lesscss_path

def pack_js():
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
        "mainConfigFile": asset("js/main.js"),
        "optimize":"none",
        "preserveLicenseComments":"false",
        "paths.requireLib": require_module,
        "include":"requireLib"
    } 
    
    optargs = " ".join("%s=%s"%(k,v)  for k,v in options.iteritems())
    local("r.js -o %s"%optargs)
    
    print("Output: %s %s"%(outfile, file_size(outfile)))
          

def pack_css():
    root = asset("less")
    hashcss = hashdir(root, "css")    
    tempfile = asset("less", hashcss)
    outfile = find_asset("css", hashcss)

    change_version( template('requirecss.html'), 
        lambda d: "<link href='{{STATIC_URL}}css/%s' rel='stylesheet' type='text/css'>"%hashcss)
      
    if os.path.exists(outfile):
        print("No change detected")
        return
     
    remove_files(find_asset("css"), r".{16}\.min.css$")
    
    infile = asset("less", "main.less")
    
    options = {
           
    }
    optargs = " ".join("--%s=%s"%(key,value) for key, value in options.iteritems())
    
    local("lessc --strict-imports %s %s > %s"%(optargs, infile, tempfile))
    
    options = {
        "cssIn": tempfile,
        "out": tempfile,
        "optimize":"uglify2",
        "preserveLicenseComments":"false"
    }
      
    optargs = " ".join("%s=%s"%(k,v)  for k,v in options.iteritems())
    local("r.js -o %s"%optargs)
    
    local("cleancss -o %s --skip-rebase -s %s"%(tempfile, tempfile))
      
    os.rename(tempfile, outfile)
    
    print("Output: %s %s"%(outfile, file_size(outfile)))
    
    
def pack_all():
    pack_css()
    pack_js()
    
def unpack_css():
    less = """
    <script>
        less = {
            environment: "development"
        };
    </script>
    <link rel="stylesheet/less" href="{{STATIC_URL}}less/main.less" />
    <script type="text/javascript" src="{{STATIC_URL}}%s#!watch"> </script>
    """%get_lesscss_path()
    change_version(template('requirecss.html'), less)

def unpack_js():
    change_version(template('requirejs.html'), "<script src='{{STATIC_URL}}%s' data-main='{{STATIC_URL}}js/main' type='text/javascript'></script>"%(get_requirejs_path()))

def unpack_all():
    unpack_css()
    unpack_js()

class Command(BaseCommand):
    
    def handle(self, mode, target="all", **options):
        if mode not in {'pack', 'unpack'}:
            raise ValueError("Unknown directive: %r"%mode)
        method_name = "%s_%s"%(mode, target)
        if not self.local:
            raise Exception("These commands should be run only on local filesystems")
        try:
            method = globals()[method_name]
        except KeyError:
            raise ValueError("Unknown target: %r"%target)
        else:
            method()

    def install_deps(self):
        subprocess.check_call("npm -g install requirejs")
        subprocess.check_call("npm -g install lesscss")
        subprocess.check_call("npm -g install bower")
        subprocess.check_call("npm -g install cleancss")
