
import threading
from django.http.request import HttpRequest
import re
import hashlib
import inspect
from datetime import date
import base64
import pickle
from django.utils.encoding import force_bytes
from django.utils import six,timezone
from django.contrib.auth import login
from django.db import models


first_cap_re = re.compile('(.)([A-Z][a-z]+)')

all_cap_re = re.compile('([a-z0-9])([A-Z])')

_context = threading.local()


__all__ = [
    'camel_to_hyphen',
    'camel_to_underscore',
    'underscore_to_camel',
    'join_with_underscore',
    'context',
    'qualified_name',
    'update_url_query',
    'get_form_name',
    'get_form_submit_name',
    'get_url_with_modified_params',
    'generate_pages',
    'calculate_age',
    'auth_login',
    'get_client_ip',
    'get_client_latlng',
    'model_from_dict',
    'base64pickle_dumps',
    'base64pickle_loads',
]


def camel_to_underscore(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def camel_to_hyphen(name):
    s1 = first_cap_re.sub(r'\1-\2', name)
    return all_cap_re.sub(r'\1-\2', s1).lower()


def join_with_underscore(*args):
    return '_'.join( str(a) for a in args if a )


def underscore_to_camel(value):
    return "".join([x.title() for x in value.split('_')])


def generate_pages(index, limit, total):
    """
    :param index: Current page number
    :param limit: Maximum number of pages
    :param total: Total number of pages
    :return: iterator of int
    """
    index = max(min(total, index), 1)
    head = int((limit-1)/2)
    tail = limit - head
    first = max(index-head, 1)
    last = min(first+limit-1, total)
    if index+tail > last:
        first -= index+tail-last-1
    return six.moves.range(max(first, 1), last+1)


def get_url_with_modified_params(request, values, append=False):
    parse = six.moves.urllib.parse
    if isinstance(request, HttpRequest):
        url = request.get_full_path()
    else:
        url = request
    parts = parse.urlsplit(url)
    params = parse.parse_qs(parts.query)
    for key, value in six.iteritems(values):
        if key not in params or not append:
            params[key] = [value]
        else:
            params[key].append(value)
    return parts._replace(query=parse.urlencode(params, True)).geturl()


def update_url_query(url, data, append=False):
    return


def qualified_name(cls):
    """
    Return fully-qualified name for classes and functions. Doesn't differentiate between
    bound and unbound methods
    :param cls:
    :return: str fully qualified name
    """
    # if hasattr(cls, "__qualname__"):
    #     return getattr(cls,"__qualname__")
    if inspect.ismodule(cls):
        return cls.__name__
    parts = [cls.__name__]
    if inspect.ismethod(cls):
        parts.append(cls.im_class.__name__)
    parts.append(cls.__module__)
    return ".".join(reversed(parts))


def create_hash(*args):
    """
    Returns a string representation of the provided arguments.
    Intended for use in other functions
    :param args: list of python objects
    :return: str
    """
    md = hashlib.md5()
    for a in args:
        md.update(repr(a))
    return md.hexdigest()


def get_form_name(form):
    if hasattr(form, 'class_oid'):
        return form.class_oid()
    if not inspect.isclass(form): form = form.__class__
    return create_hash(qualified_name(form))


def get_form_submit_name(form):
    if hasattr(form, 'submit_name'):
        return form.submit_name()
    return "submit-%s"%get_form_name(form)


def context():
    return _context


def set_local(key, value):
    ctx = context()
    setattr(ctx, key, value)


def get_local(key, default=None):
    ctx = context()
    return getattr(ctx, key, default)

def auth_login(request,user):
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request,user)
    return user

def calculate_age(born):
    today = timezone.now().date()
    if not born: return 0
    try: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year)
    except ValueError:
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def settings_reloader(global_vars, prefix):
    def refresh():
        from django.conf import settings
        for key in global_vars:
            if key.startswith(prefix):
                if hasattr(settings, key):
                    global_vars[key] = getattr(settings, key)
    refresh(globals, prefix)
    return refresh


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_latlng(request):
    from django.contrib.gis.geoip import GeoIP
    g = GeoIP()
    ip = get_client_ip(request)
    return g.lat_lon(ip)


def model_from_dict(model, **kwargs):
    meta = model._meta
    names = set( meta.get_all_field_names() )
    names.difference_update({a.name for a in meta.many_to_many})
    return model(**dict((k, v) for k, v in six.iteritems(kwargs) if k in names))


def update_object(instance, data):
    opts = instance._meta
    file_field_list = []
    # Wrap up the saving of m2m data as a function.
    def save_m2m():
        for f in opts.many_to_many:
            if f.name in data:
                f.save_form_data(instance, data[f.name])

    for f in opts.fields:
        if f.name not in data or isinstance(f, models.AutoField):
            continue
        if isinstance(f, models.FileField):
            file_field_list.append(f)
        else:
            f.save_form_data(instance, data[f.name])

    for f in file_field_list:
        f.save_form_data(instance, data[f.name])

    return save_m2m


def base64pickle_loads(data):
    encoded_data = base64.b64decode(force_bytes(data))
    return pickle.loads(encoded_data)


def base64pickle_dumps(data):
    serialized = pickle.dumps(data)
    return base64.b64encode(serialized).decode("ascii")
