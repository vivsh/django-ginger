from collections import namedtuple
import inspect
import operator
from django.utils.encoding import force_text
from django.template import loader
from django.utils.safestring import mark_safe
from jinja2 import Markup
import re
from collections import OrderedDict
import json
import functools
from django.forms.forms import BoundField
from django.utils import six
from ginger import utils, serializer

__all__ = [
    "add_link_builder",
    "get_link_builder",
    "GingerNav",
    "build_links",
    "flatten_attributes",
    "create_css_class",
    "Link",
    "LinkList",
    "LinkTree",
    "UIComponent",
    "as_json"
]

_link_builders = {}


class Link(object):

    has_links = False
    is_authorized = True

    def __init__(self, url, content, is_active=False, **kwargs):
        self.url = url
        self.content = content
        self.is_active = is_active
        for k in kwargs:
            setattr(self, k, kwargs[k])



class LinkList(object):

    has_links = True

    def __init__(self, url=None, content="", is_active=False, **kwargs):
        self.url = url
        self.content = content
        self.is_active = is_active
        for k in kwargs:
            setattr(self, k, kwargs[k])
        self.links = []

    def append(self, link):
        self.links.append(link)

    def extend(self, links):
        self.links.extend(links)

    def __len__(self):
        return len(self.links)

    def __iter__(self):
        return iter(self.links)


class LinkTree(object):

    def __init__(self, folder=None):
        self.root = OrderedDict() if folder is None else folder

    def child(self, path):
        fragments = self.split(path)
        folder = self.root
        previous = None
        for f in fragments:
            if not isinstance(folder, dict):
                d = OrderedDict()
                d[previous[1]] = folder
                previous[0][previous[1]] = d
                folder = d
            if f not in folder:
                folder[f] = OrderedDict()
            previous = folder, f
            folder = folder[f]
        if not isinstance(folder, dict):
            raise ValueError("Invalid folder path: %r. The path value refers to a file." % path)
        return LinkTree(folder) if fragments else self

    def add(self, label, url):
        folder = self.root
        if url in folder:
            raise ValueError("Key %r already exists" % label)
        folder[label] = url

    def extend(self, items):
        for label, url in items:
            self.add(label, url)

    def split(self, path):
        if not path:
            path = ""
        return [p for p in re.sub('/+', '/', path.strip("/ ")).split("/") if p]

    def _make_links(self, path_info, store):
        result = []
        for label, data in store.iteritems():
            if isinstance(data, dict):
                node = LinkList(content=label)
                children = self._make_links(path_info, data)
                node.extend(children)
            else:
                is_active = path_info == data
                node = Link(content=label, url=data, is_active=is_active)
            result.append(node)
        return result

    def build_links(self, request):
        path_info = request.path_info
        return self._make_links(path_info, self.root)




def add_link_builder(cls, build_func):
    _link_builders[cls] = build_func


def get_link_builder(obj):
    cls = obj.__class__ if not isinstance(obj, type) else obj
    if hasattr(obj, 'build_links'):
        return obj.build_links
    else:
        try:
            func = _link_builders[cls]
        except KeyError:
            raise TypeError("No link builder associated with %r"%cls)
        else:
            return functools.partial(func, obj)


def build_links(obj, request, unique=True):
    builder = get_link_builder(obj)
    history = set()
    for link in builder(request):
        if unique and link.content in history:
            continue
        history.add(link.content)
        yield link


def is_selected_choice(values, choice):
    if not isinstance(values, (list, tuple)):
        values = (values, )
    text_choice = force_text(choice)
    for v in values:
        if v == choice or text_choice == force_text(v):
            return True
    return False


Choice = namedtuple("Choice", ["name", "value", "content", "selected"])

def bound_field_choices(field):
    form_field = field.field
    field_value = field.value()
    name = field.html_name
    for code, label in form_field.choices:
        is_active = is_selected_choice(field_value, code)
        yield Choice(name, code, label, is_active)

def bound_field_link_builder(field, request):
    url = request.get_full_path()
    form_field = field.field
    field_value = field.value()
    if hasattr(form_field, 'build_links'):
        for value in form_field.build_links(request, field):
            yield value
    else:
        for code, label in form_field.choices:
            is_active = is_selected_choice(field_value, code)
            link_url = utils.get_url_with_modified_params(url, {field.name: code})
            yield Link(link_url, label, is_active, value=code)


class GingerNav(object):

    def __init__(self, *links):
        self.links = []
        for link in links:
            self.add_link(**link)

    def add_link(self, url, content, **kwargs):
        link = {
            "url": url,
            "content": content
        }
        link.update(kwargs)
        self.links.append(link)

    def build_links(self, request):
        base_url = request.get_full_path()
        for link in self.links:
            url = link['url']
            is_active = url == base_url
            yield Link(is_active=is_active, **link)


add_link_builder(BoundField, bound_field_link_builder)


def create_css_class(*classes):
    history = set()
    frags = re.split(r'\s+', " ".join(classes).strip())
    result = []
    for value in frags:
        if value and value not in history:
            result.append(value)
            history.add(value)
    return ' '.join(result)


def flatten_attributes(attrs):
    result = []
    css = []
    for k, v in six.iteritems(attrs):
        if k == 'class':
            css.append(v)
            continue
        if isinstance(v, basestring):
            v = str(v).encode('string-escape')
        else:
            v = json.dumps(v)
        result.append("%s='%s'"% (k,v))
    css = create_css_class(*css)
    if css:
        result.append("class=%s" % css)
    return " ".join(result)


def choices_to_options(request, bound_field):
    tags = []
    for link in build_links(bound_field, request):
        selected = "selected" if link.is_active else ""
        html = "<option value='%s' %s> %s </option>" % (link.value, selected, link.content)
        tags.append(html)
    return Markup("".join(tags))


class Entry(object):

    __position = 1

    def __init__(self, view, **kwargs):
        self.view = view
        Entry.__position += 1
        self.position = self.__position
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __getattr__(self, key):
        return getattr(self.view, key)

    def get_url(self, request, *args, **kwargs):
        return self.view.reverse(*args, **kwargs)


class BoundEntry(object):

    def __init__(self, entry):
        self.entry = entry


class Navigation(object):

    def __init__(self, request, args, kwargs):
        super(Navigation, self).__init__()
        self.request = request
        self.args = args
        self.kwargs = kwargs

    def _get_entries(self):
        return sorted(inspect.getmembers(self, lambda v: isinstance(v, Entry)), key=operator.attrgetter("position"))

    def entries(self):
        for entry in self._get_entries():
         if self.accept(entry, self.request):
             yield entry

    def __iter__(self):
        return self.entries()

    def accept(self, entry, request):
        return True


def as_json(values):
    content = serializer.encode(values)
    return Markup(content)


class UIComponent(object):

    template_name = None

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        return kwargs

    def render(self, context, **kwargs):
        ctx = {}
        template_names = self.get_template_names()
        ctx.update(context)
        ctx.update(kwargs)
        return mark_safe(loader.render_to_string(template_names, context=ctx))

