# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loaders import app_directories
from django.template.loaders import filesystem
from django_jinja.base import env
import jinja2
import os

JINJA_TEMPLATE_EXTENSION = getattr(settings, 'JINJA_TEMPLATE_EXTENSION', '.jinja')

JINJA_EXCLUDE_FOLDERS = set(getattr(settings,'JINJA_EXCLUDE_FOLDERS',()))


class LoaderMixin(object):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        """
        In the root directory, use jinja only for files with jinja extension
        In app directory, use it for all
        """
        root = template_name.strip("/").split("/",1)[0]
        _,ext  = os.path.splitext(template_name) 
        if root not in JINJA_EXCLUDE_FOLDERS or ext == JINJA_TEMPLATE_EXTENSION:
            try:
                template = env.get_template(template_name)
                return template, template.filename
            except jinja2.TemplateNotFound:            
                raise TemplateDoesNotExist(template_name)                    
        else:                
            return super(LoaderMixin, self).load_template(template_name, template_dirs)        


class FileSystemLoader(LoaderMixin, filesystem.Loader):
    pass


class AppLoader(LoaderMixin, app_directories.Loader):
    pass