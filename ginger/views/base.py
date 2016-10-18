import inspect
import re
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured, PermissionDenied
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.utils.text import camel_case_to_spaces
from django.views.generic.base import View
from django.conf.urls import url
from django.utils import six
from .meta import ViewInfo
from ginger import utils, pattern


__all__ = ["GingerView", "GingerViewSetMixin", 'view']


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

    def as_url(self, prefix=None, **kwargs):
        view_func = self.view.as_view(**kwargs)
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
    __actions = None

    def __init__(cls, name, bases, attrs):
        super(GingerMetaView, cls).__init__(name, bases, attrs)
        GingerMetaView.__position += 1
        cls.position = GingerMetaView.__position
        cls.__abstract__ = attrs.get("__abstract__", False)
        cls.base_name = "_".join(camel_case_to_spaces(re.sub(r'(?i)view.*', '', cls.__name__)).split())


class BasicView(View, GingerSessionDataMixin):

    DEBUG = messages.DEBUG
    INFO = messages.INFO
    WARNING = messages.WARNING
    ERROR = messages.ERROR
    SUCCESS = messages.SUCCESS

    url_name = None

    url_prefix = None

    url_regex = None

    action = None

    context_object_key = "object"

    session_key_prefix = ""

    @classmethod
    def as_view(cls, **initkwargs):
        func = super(BasicView, cls).as_view(**initkwargs)
        func.view_class = cls
        cls.setup_view()
        return func

    @classmethod
    def setup_view(cls):
        pass

    def get_user(self):
        return self.request.user

    def get_ip(self):
        return utils.get_client_ip(self.request)

    def process_request(self, request):
        self.user = self.get_user()

    def process_response(self, request, response):
        return response

    def process_exception(self, request, ex):
        pass

    def dispatch(self, request, *args, **kwargs):
        try:
            response = self.process_request(request)
            if not response:
                response = super(BasicView, self).dispatch(request, *args, **kwargs)
        except Exception as ex:
            response = self.process_exception(request, ex)
            if response is None:
                raise
        response = self.process_response(request, response)
        return response

    def get_context_data(self, **kwargs):
        if 'view' not in kwargs:
            kwargs['view'] = self
        return kwargs

    def add_message(self,  message, level=messages.INFO, **kwargs):
        if not message:
            return
        messages.add_message(self.request, level, message, **kwargs)

    def get_messages(self):
        return messages.get_messages(self.request)

    def get_previous_url(self, default=None):
        return self.request.META.get("HTTP_REFERER", default)


@six.add_metaclass(GingerMetaView)
class GingerView(BasicView, GingerSessionDataMixin):

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

    def get_target(self):
        return None

    @classmethod
    def is_authorized(cls, user, resource=None):
        return True

    def process_request(self, request):
        super(GingerView, self).process_request(request)
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

    @classmethod
    def create_url_regex(cls):
        return "%s/" % cls.meta.url_verb

    def get_context_data(self, **kwargs):
        kwargs = super(GingerView, self).get_context_data(**kwargs)
        if hasattr(self, "object") and "object" not in kwargs:
            kwargs[self.context_object_key] = self.object
        return kwargs


class SubView(object):
    many = False
    suffix = None
    regex = None

    def __init__(self, name, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
        self.name = name
        if self.suffix is None:
            self.suffix = self.name


def view(fn=None, **kwargs):
    if kwargs and fn:
        raise TypeError("Only keyword arguments are accepted")

    def wrapper(func):
        func.subview = SubView(name=func.__name__, **kwargs)
        return func

    if not kwargs and callable(fn):
        return wrapper(fn)

    return wrapper


def get_child_views(cls):
    for name, func in inspect.getmembers(cls):
        if callable(func) and hasattr(func, 'subview'):
            yield func.subview


class GingerViewSetMixin(object):

    def check_object_permissions(self, obj):
        pass

    def check_user_permissions(self):
        pass

    @classmethod
    def reverse(cls, action_name, *args, **kwargs):
        url_prefix = cls.base_name
        url_name = "%s_%s" % (url_prefix, action_name)
        return reverse(url_name, kwargs=kwargs, args=args)

    def get(self, request, *args, **kwargs):
        self.check_user_permissions()
        return getattr(self, self.action)(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.check_user_permissions()
        return getattr(self, self.action)(request, *args, **kwargs)

    def process_response(self, request, response):
        if isinstance(response, dict):
            response = self.render_to_response(self.get_context_data(**response))
        return response

    @classmethod
    def as_urls(cls, **kwargs):
        result = []
        base_name = cls.base_name
        for subview in get_child_views(cls):
            regex = cls.url_prefix
            if not subview.many:
                regex = "%sobject_id:int/" % regex
            if subview.suffix:
                regex = "%s%s/" % (regex, subview.suffix,)
            if subview.regex:
                regex = "%s%s" % (regex, subview.regex)
            url_regex = pattern.Pattern(regex).create()
            url_name = "_".join([base_name, subview.name]).lower()
            view_class = url(url_regex, cls.as_view(
                action=subview.name,
                url_name=url_name,
                url_regex=url_regex,
                **kwargs
            ), name=url_name)
            result.append(view_class)
        return result

    def get_template_names(self):
        template_name = self.template_name
        return [template_name.format(action=self.action)]