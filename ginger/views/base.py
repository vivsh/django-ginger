from django.utils.functional import cached_property
import re
import os

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.views.generic.base import View
from django.conf.urls import url

from ginger import utils


__all__ = ["P", "GingerView"]


class Num(object):

    def match(self, value):
        return value == 'num'

    def pattern(self, value):
        return r'\d+'


class Slug:

    def match(self, value):
        return value == "slug"

    def pattern(self, value):
        return r'[a-z0-9A-Z][a-zA-Z0-9\-]*'


class Name:

    def match(self, value):
        return value == "name"

    def pattern(self, value):
        return r'[a-zA-Z]\w+'


class Choice:

     def match(self, value):
         return value.startswith("(") and value.endswith(")")

     def pattern(self, value):
         parts = value.strip("()").split(",")
         return "|".join(p.strip() for p in parts)


class Pattern(object):

    pattern_types = [Num, Slug, Name, Choice]

    def __init__(self, value):
        self.value = value

    def match(self, value):
        for cls in self.pattern_types:
            p = cls()
            if p.match(value):
                return p.pattern(value)
        return value

    def __str__(self):
        return self.create()

    def create(self):
        parts = re.sub("/+", "/", self.value).lstrip("/").split("/")
        result = []
        size = len(parts)
        for i, p in enumerate(parts):
            slash = "" if i == size-1 else "/"
            if ":" not in p:
                if p:
                    p = "%s%s" % (p, slash)
                result.append(p)
            else:
                opt = False
                name, pattern = p.split(":", 1)
                if name.endswith("?"):
                    name = name[:-1]
                    opt = True
                pattern = self.match(pattern)
                pattern = r"(?P<%s>%s)%s" % (name, pattern, slash)
                if opt:
                    pattern = r"(?:%s)?" % pattern
                result.append(pattern)
        return r"^%s$" % "".join(result)

    def compile(self, **kwargs):
        return re.compile(self.create(), **kwargs)

    def findall(self, text, **kwargs):
        rx = self.compile(**kwargs)
        return rx.findall(text)

P = Pattern


class ViewMeta(object):

    def __init__(self, view):
        super(ViewMeta, self).__init__()
        self.view = view

    @cached_property
    def app(self):
        from django.apps import apps
        app = apps.get_containing_app_config(utils.qualified_name(self.view))
        return app

    def url_name(self):
        name = utils.camel_to_underscore(self.view.__name__).replace("_view", "").strip("_")
        return name

    def template_dir(self):
        folder = self.app.path
        return os.path.join(folder, "templates")

    def template_name(self):
        name = "%s/%s.html" % (self.app.label, self.url_name())
        return name

    def template_path(self):
        return os.path.join(self.template_dir(), self.template_name())

    def form_name(self):
        parts = self.url_name().split("_")
        parts.append("Form")
        return "".join(p.capitalize() for p in parts)

    def form_path(self):
        return os.path.join(self.app.path, "forms.py")

    @property
    def verb(self):
        return self.name.split("-")[-1]

    def url_regex(self):
        return self.view.url_regex

    def as_url(self):
        view_func = self.view.as_view()
        regex = self.url_regex()
        url_name = self.url_name()
        return url(str(regex), view_func, name=url_name)

    def reverse(self, args, kwargs):
        return reverse(self.url_name(), args=args, kwargs=kwargs)



class ViewMetaDescriptor(object):

    def __get__(self, obj, owner=None):
        instance = owner or obj
        try:
            result = instance.__meta
        except AttributeError:
            result = ViewMeta(instance)
            instance.__meta = result
        return result



class GingerSessionDataMixin(object):

    session_key_prefix = ""

    def get_session_key(self):
        host = self.request.get_host()
        return "%s-%s-%s" % (self.session_key_prefix, host, self.class_oid())

    def get_session_data(self):
        return self.request.session.get(self.get_session_key())

    def set_session_data(self, data):
        self.request.session[self.get_session_key()] = data

    def clear_session_data(self):
        self.request.session.pop(self.get_session_key(), None)

    @classmethod
    def class_oid(cls):
        return utils.create_hash(utils.qualified_name(cls))


class GingerView(View, GingerSessionDataMixin):

    user = None

    url_regex = P("home/")

    meta = ViewMetaDescriptor()


    @classmethod
    def as_url(cls):
        return cls.meta.as_url()

    @classmethod
    def reverse(cls, *args, **kwargs):
        return cls.meta.reverse(*args, **kwargs)

    @classmethod
    def as_view(cls, **initkwargs):
        func = super(GingerView, cls).as_view(**initkwargs)
        cls.setup_resource()
        return func

    @classmethod
    def setup_resource(cls):
        return

    def get_user(self):
        return self.request.user

    def process_request(self, request):
        self.user = self.get_user()
        if hasattr(self, 'get_object'):
            try:
                self.object = self.get_object()
            except ObjectDoesNotExist:
                raise Http404
        elif hasattr(self, 'get_queryset'):
            self.queryset = self.get_queryset()

    def process_response(self, request, response):
        return response

    def process_exception(self, request, ex):
        return

    def dispatch(self, request, *args, **kwargs):
        try:
            response = self.process_request(request)
            if not response:
                response = super(GingerView, self).dispatch(request, *args, **kwargs)
        except Exception as ex:
            response = self.process_exception(request, ex)
            if not response:
                raise
        response = self.process_response(request, response)
        return response


    def get_context_data(self, **kwargs):
        if 'view' not in kwargs:
            kwargs['view'] = self
        return kwargs

    def add_message(self, level, message, **kwargs):
        if not message:
            return
        messages.add_message(self.request, level, message, **kwargs)

if __name__ == '__main__':
    val = r"/any/any:num/some:slug/another:(first,second,third)/block/"
    p = Pattern(val)
    rx = p.compile()
    print p
    print rx.findall("any/1234/Thirs-343-67-90-yuyu/first/block/")


