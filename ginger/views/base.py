
import os
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.views.generic.base import View
from django.conf.urls import url
from django.utils import six
from .meta import ViewInfo
from ginger import utils, pattern


__all__ = ["P", "GingerView"]



P = pattern.Pattern


class ViewMeta(ViewInfo):

    def __init__(self, view, viewset=None):
        from django.apps import apps
        app = apps.get_containing_app_config(utils.qualified_name(view))
        super(ViewMeta, self).__init__(app, view.__name__)
        self.view = view
        self.viewset = viewset

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

    def as_url(self, **kwargs):
        view_func = self.view.as_view()
        regex = self.url_regex
        url_name = self.url_name
        regex = pattern.Pattern(regex).create() if not isinstance(regex, pattern.Pattern) else regex.create()
        return url(regex, view_func, name=url_name, kwargs=kwargs)

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


@six.add_metaclass(GingerMetaView)
class GingerView(View, GingerSessionDataMixin):

    user = None

    url_regex = None

    url_prefix = None

    context_object_key = "object"

    meta = ViewMetaDescriptor()


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
        return

    def get_target(self):
        return None

    def get_user(self):
        return self.request.user

    def get_ip(self):
        return utils.get_client_ip(self.request)

    def process_request(self, request):
        self.user = self.get_user()
        if hasattr(self, 'get_object'):
            try:
                self.object = self.get_object()
            except ObjectDoesNotExist:
                raise Http404
        elif hasattr(self, 'get_queryset'):
            self.queryset = self.get_queryset()
        self.target = self.get_target()

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
