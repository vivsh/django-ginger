import inspect
import os
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, PermissionDenied
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.views.generic.base import View
from django.conf.urls import url, patterns
from django.utils import six
from .meta import ViewInfo
from ginger import utils, pattern


__all__ = ["P", "GingerView", "GingerViewSet", "GingerSubView"]



P = pattern.Pattern


class ViewMeta(ViewInfo):

    def __init__(self, view):
        from django.apps import apps
        app = apps.get_containing_app_config(utils.qualified_name(view))
        super(ViewMeta, self).__init__(app, view.__name__)
        self.view = view

    @property
    def url_regex(self):
        regex = self.view.url_regex
        if regex is None:
            regex = self.view.create_url_regex()
        if regex is None:
            raise ImproperlyConfigured("%s cannot have a None url pattern" % self.view.__name__)
        prefix = self.view.url_prefix
        if prefix:
            regex = "%s%s" % (prefix, regex)
        return regex

    def as_url(self, prefix=None, parent=None, **kwargs):
        view_func = self.view.as_view(parent=parent, **kwargs)
        regex = self.url_regex
        url_name = self.url_name
        regex = pattern.Pattern(regex, prefix).create()
        if prefix:
            url_name = "%s_%s" % (prefix, url_name)
        return url(regex, view_func, name=url_name)

    def reverse(self, args, kwargs):
        return reverse(self.url_name, args=args, kwargs=kwargs)



class ViewMetaDescriptor(object):

    def __init__(self, **kwargs):
        super(ViewMetaDescriptor, self).__init__()
        self.kwargs = kwargs
        self.hash_code = hash(tuple(sorted(kwargs.items(), key=lambda a,b: a)))

    def __get__(self, obj, owner=None):
        instance = owner or obj
        key = "_%s_%s_%s" % (instance.__name__, self.__class__.__name__, self.hash_code)
        try:
            result = getattr(instance, key)
        except AttributeError:
            result = ViewMeta(instance, **self.kwargs)
            setattr(instance, key, result)
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


class GingerMetaView(type):

    __position = 0

    def __init__(cls, name, bases, attrs):
        super(GingerMetaView, cls).__init__(name, bases, attrs)
        GingerMetaView.__position += 1
        cls.position = GingerMetaView.__position
        cls.__abstract__ = attrs.get("__abstract__", False)



@six.add_metaclass(GingerMetaView)
class GingerView(View, GingerSessionDataMixin):

    user = None

    parent = None

    url_regex = None

    url_prefix = None

    context_object_key = "object"

    meta = ViewMetaDescriptor()

    @classmethod
    def instantiate(cls, request, **kwargs):
        instance = cls()
        instance.request = request
        instance.args = ()
        instance.kwargs = kwargs
        instance.user = kwargs.pop("user", request.user)
        if 'object' in kwargs:
            instance.object = kwargs.pop("object")
        return instance

    @classmethod
    def as_url(cls, **kwargs):
        url = cls.meta.as_url(**kwargs)
        return url

    @classmethod
    def reverse(cls, *args, **kwargs):
        return cls.meta.reverse(args, kwargs)

    @classmethod
    def as_view(cls, **initkwargs):
        func = super(GingerView, cls).as_view(**initkwargs)
        func.view_class = cls
        cls.setup_view()
        return func

    @classmethod
    def setup_view(cls):
        # if cls.url_regex is None:
        #     raise ImproperlyConfigured("No url regex has been specified for %r" % cls)
        if not (inspect.ismethod(cls.is_authorized) and cls.is_authorized.__self__ is cls):
            raise ImproperlyConfigured("is_authorized should be a classmethod in %r" % cls)

    def get_target(self):
        return None

    def get_user(self):
        return self.request.user

    def get_ip(self):
        return utils.get_client_ip(self.request)

    @classmethod
    def is_authorized(cls, user, resource=None):
        return True

    def process_request(self, request):
        self.user = self.get_user()
        if not self.is_authorized(self.user):
            raise PermissionDenied
        if hasattr(self, 'get_object'):
            try:
                self.object = self.get_object()
            except ObjectDoesNotExist:
                raise Http404
        elif hasattr(self, 'get_queryset'):
            self.queryset = self.get_queryset()
        self.target = self.get_target()
        if hasattr(self, 'object') and not self.is_authorized(self.user, self.object):
            raise PermissionDenied

    def process_response(self, request, response):
        return response

    def process_exception(self, request, ex):
        pass

    def dispatch(self, request, *args, **kwargs):
        try:
            response = self.process_request(request)
            if not response:
                response = super(GingerView, self).dispatch(request, *args, **kwargs)
        except Exception as ex:
            response = self.process_exception(request, ex)
            if response is None:
                raise
        response = self.process_response(request, response)
        return response

    @classmethod
    def create_url_regex(cls):
        return "%s/" % cls.meta.url_verb

    def get_context_data(self, **kwargs):
        if 'view' not in kwargs:
            kwargs['view'] = self
        if hasattr(self, "object") and "object" not in kwargs:
            kwargs[self.context_object_key] = self.object
        return kwargs

    def add_message(self,  message, level=messages.INFO, **kwargs):
        if not message:
            return
        messages.add_message(self.request, level, message, **kwargs)

    def get_messages(self):
        return messages.get_messages(self.request)



class GingerSubView(object):

    __position = 0
    name = None

    def __init__(self, view_class, **kwargs):
        self.view_class = view_class
        self.kwargs = kwargs
        GingerSubView.__position += 1
        self.position = GingerSubView.__position

    def subclass(self, prefix, regex):
        name = self.name
        meta = self.view_class.meta
        child_verb = meta.url_verb
        parts = meta.url_name.replace(child_verb, name, 1).split("-")
        parts.insert(0, prefix)
        class_name = "".join(a.capitalize() for a in parts)
        child_regex = meta.url_regex.replace(child_verb, name, 1)
        regex = "%s/%s" % (regex, child_regex)
        ctx = self.kwargs.copy()
        ctx['url_regex'] = regex
        new_class = type(class_name, (self.view_class,), ctx)
        return new_class


@six.add_metaclass(GingerMetaView)
class GingerViewSet(object):

    url_regex = None

    @classmethod
    def get_subviews(cls):
        for name, subview in inspect.getmembers(cls, lambda a: isinstance(a, GingerSubView)):
            subview.name = name
            yield subview

    @classmethod
    def as_urls(cls):
        instance = cls()
        result = []
        prefix = cls.__name__.replace("ViewSet", "")
        for sub in sorted(cls.get_subviews(), key=lambda s: s.position):
            result.append(sub.subclass(prefix, cls.url_regex).as_url(parent=instance))
        return result

    @classmethod
    def as_patterns(cls, prefix=""):
        return patterns(prefix, *cls.as_urls())

    def get_template_names(self, view, **kwargs):
        return ()

    def get_context_view(self, view, **kwargs):
        return ()

