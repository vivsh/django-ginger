from django.utils.encoding import force_text
import re
from django.utils import six
from ginger import serializer
from jinja2 import Markup


__all__ = ['html_json', 'html_attrs', "Element", "CssClassList", "CssStyle", 'add_css_class', 'empty']


def html_json(values):
    content = serializer.encode(values)
    try:
        content = content.encode("unicode-escape")
    except LookupError:
        content = content.encode("string-escape")
    return Markup(content)


def html_attrs(*args, **kwargs):
    attr = HtmlAttr()
    attr.update(*args, **kwargs)
    return six.text_type(attr)


def add_css_class(original_class, *css_classes):
    css = CssClassList()
    css.append(original_class)
    css.append(css_classes)
    return six.text_type(css)


class CssClassList(object):

    def __init__(self):
        self.classes = []

    def __iter__(self):
        return iter(self.classes)

    def __len__(self):
        return len(self.classes)

    def copy(self):
        value = CssClassList()
        value.classes.extend(self.classes)
        return value

    def append(self, value):
        if isinstance(value, six.text_type):
            value = re.sub(r'\s+', ' ', value.strip())
            if len(value) == 1:
                value = value[0]
        if isinstance(value, (tuple, list)):
            for val in value:
                self.append(val)
        else:
            if value not in self.classes:
                self.classes.append(value)

    def __contains__(self, item):
        return item in self.classes

    def __str__(self):
        return " ".join(self.classes)


class CssStyle(dict):

    def __str__(self):
        return ";".join("%s:%s"%p.replace("_", "-") for p in six.iteritems(self.items))


def _normalize(key):
    if key.endswith("_"):
        key = key[:-1]
    key = key.replace("__", ":").replace("_", "-")
    return key


class HtmlAttr(object):

    def __init__(self):
        self.attrs = {}
        self.styles = CssStyle()
        self.classes = CssClassList()

    def copy(self):
        attr = HtmlAttr()
        attr.attrs = self.attrs.copy()
        attr.styles = self.styles.copy()
        attr.classes = self.classes.copy()
        return attr

    def dict(self):
        return dict(self)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, item):
        return dict(self)[item]

    def __len__(self):
        return len(dict(self))

    def get(self, key):
        return dict(self).get(key)

    def set(self, key, value):
        key = _normalize(key)
        if key in {"class"}:
            self.classes.append(value)
        elif key == "style":
            self.styles.update(value)
        else:
            self.attrs[key] = value

    def update(self, *args, **attrs):
        values = {}
        values.update(*args, **attrs)
        for k, v in values.items():
            self.set(k, v)

    def __iter__(self):
        for k, v in six.iteritems(self.attrs):
            yield k, v
        if self.classes:
            yield "class", six.text_type(self.classes)
        if self.styles:
            yield "style", six.text_type(self.styles)

    def render(self):
        pairs = []
        for key, value in self:
            if value is None or value is False:
                continue
            if value is True:
                pairs.append(key)
            else:
                if not isinstance(value, six.string_types):
                    value = html_json(value)
                pairs.append("%s='%s'" % (key, value))
        return " ".join(pairs)

    def __str__(self):
        return self.render()


class Element(object):

    def __init__(self, tag):
        self.tag = tag
        self.attrib = HtmlAttr()
        self.children = []

    def __call__(self, **kwargs):
        el = self.copy()
        el.attrib.update(kwargs)
        return el

    def __getitem__(self, item):
        el = self.copy()
        if not isinstance(item, (list, tuple)):
            item = [item]
        for c in item:
            el.append(c)
        return el

    def copy(self):
        el = self.__class__(self.tag)
        el.attrib = self.attrib.copy()
        el.children = self.children[:]
        return el

    def mutate(self, tag):
        el = tag.copy()
        el.attrib.update(self.attrib.copy())
        el.children = self.children[:]
        return el

    def append(self, child):
        if child is None:
            return
        if isinstance(child, (list, tuple)):
            for c in child:
                self.append(c)
        else:
            self.children.append(child)

    def convert_to_text(self, el, *args, **kwargs):
        return el.render(*args, **kwargs) if hasattr(el, 'render') else force_text(el)

    def render_children(self, *args, **kwargs):
        return "".join(self.convert_to_text(c, *args, **kwargs)for c in self.children)

    def render(self, ctx=None):
        attrs = self.attrib
        content = self.render_children(ctx)
        tag = _normalize(self.tag)
        return u"<{tag} {attrs}>{content}</{tag}>".format(**locals())

    def __str__(self):
        return self.render()

    def __html__(self):
        return self.render()


class Empty(Element):
    def render(self, *args, **kwargs):
        return self.render_children(*args, **kwargs)

empty = Empty("none")

for name in "html body link meta div span form section article aside main ul li ol dl dd dt p a strong "\
            "i fieldset legend b em input select button label nav textarea".split(" "):
    __all__.append(name)
    globals()[name] = Element(name)


if __name__ == '__main__':
    print(input(type="radio", checked=False).render())