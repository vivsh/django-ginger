

from django.utils import six

import hashlib
import inspect

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
    return six.moves.range(max(first,1), last+1)


def get_url_with_modified_params(request, values, append=False):
    parse = six.moves.urllib.parse
    if not isinstance(request, six.text_type):
        url = request.get_full_path()
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
    if hasattr(cls, "__qualname__"):
        return getattr(cls,"__qualname__")
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

