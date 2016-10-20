from django.utils import six

import re
from collections import deque


__all__ = ["u", "Component"]


_RX_TAG = re.compile(r'([.  # ]?[^\s#.]+)')

component_registry = {}


def styles_to_string(value):
    if isinstance(value, str):
        return value
    return ";".join("%s:%s" % (key.replace("_", "-"), value) for (key, value) in value.items())


class Tag(object):

    __slots__ = ['name', 'attrib', 'children']

    def __init__(self, name, attrib, children):
        self.name = name
        self.attrib = attrib
        self.children = children

    def __iter__(self):
        for child in self.children:
            yield child

    def start_tag(self):
        name = self.name
        attrib = self.attrib
        result = []
        for key, value in attrib.items():
            if key.endswith("_"):
                key = key[:-1]
            key = key.replace("_", "-")
            if key == 'class':
                value = declassify(value)
            elif key == 'style':
                value = styles_to_string(value)
            pair = "%s='%s'" % (key, value)
            result.append(pair)
        attrib = " ".join(result)
        attrib = " %s" % attrib if attrib else ""
        return "<%s%s>" % (name, attrib)

    def end_tag(self):
        return "</%s>" % self.name


def camel_to_hyphen(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()



class MetaComponent(type):

    def __init__(cls, name, bases, attrs):
        super(MetaComponent, cls).__init__(name, bases, attrs)
        tag_name = camel_to_hyphen(name)
        component_registry[tag_name] = cls


@six.add_metaclass(MetaComponent)
class Component(object):

    def __init__(self, attrib, children):
        self.children = children
        self.attrib = attrib

    def render(self, context):
        raise NotImplementedError


def declassify(*args):
    stack = deque(args)
    history = set()
    result = []
    while stack:
        item = stack.popleft()
        if isinstance(item, (tuple, list)):
            item = list(item)
            item.reverse()
            stack.extendleft(item)
        elif isinstance(item, dict):
            for key, value in item.items():
                if value:
                    stack.appendleft(key)
        elif isinstance(item, str):
            parts = item.split()
            for p in parts:
                if p and p not in history:
                    history.add(p)
                    result.append(p)
        elif item is not None:
            stack.appendleft(str(item))
    return " ".join(result)


def parse_tag(value, attrs):
    parts = deque(_RX_TAG.split(value))
    tag = "div"
    history = set()
    classes = []

    while parts:
        item = parts.popleft()
        if item:
            if item[0] == '.':
                item = item[1:]
                if item not in history:
                    classes.append(item)
                    history.add(item)
            elif item[0] == '#':
                item = item[1:]
                attrs["id"] = item
            else:
                tag = item

    if classes:
        if 'class' in attrs :
            attrs['class'] = declassify(classes, attrs['class'])
        else:
            attrs['class'] = " ".join(classes)

    return tag


def stringify(tag, context):
    output = []
    stack = deque([tag])
    while stack:
        item = stack.pop()
        if isinstance(item, Tag):
            output.append(item.start_tag())
            stack.append(item.end_tag())
            stack.extend(item)
        elif isinstance(item, Component):
            stack.append(item.render(context))
        elif item is not None:
            output.append(str(item))
    return "".join(output)


def u(tag, *args, **kwargs):
    attrs = {k.rstrip("_"): v for k,v in kwargs.items()}
    children = []

    if not attrs.pop("if", True):
        return None

    stack = deque(args)

    while stack:
        item = stack.pop()
        if isinstance(item, (tuple, list)):
            stack.extend(item)
        elif isinstance(item, (Component, Tag)):
            children.append(item)
        elif item is not None:
            children.append(item)

    if not callable(tag):
        tag = parse_tag(tag, attrs)
        if tag in component_registry:
            tag = component_registry[tag]

    if callable(tag):
        return tag(attrs, children)
    else:
        return Tag(tag, attrs, children)


