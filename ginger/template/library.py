import functools
from django.utils import six
import jinja2
from ginger.utils import camel_to_underscore
from .backend import library_functions


__all__ = ['function_tag', 'filter_tag', 'test_tag', 'ginger_tag']


def _attach_function(attr, func, name=None):
    if name is None:
        name = func.__name__
    library_functions.append((attr, name, func))
    return func


def _register_function(attr, name=None, fn=None):
    if name is None and fn is None:
        def dec(func):
            return _attach_function(attr, func)
        return dec

    elif name is not None and fn is None:
        if callable(name):
            return _attach_function(attr, name)
        else:
            def dec(func):
                return _register_function(attr, name, func)
            return dec

    elif name is not None and fn is not None:
        return _attach_function(attr, fn, name)

    raise RuntimeError("Invalid parameters")


def global_function(*args, **kwargs):
    return _register_function("globals", *args, **kwargs)


def test(*args, **kwargs):
    return _register_function("tests", *args, **kwargs)


def filter(*args, **kwargs):
    return _register_function("filters", *args, **kwargs)


def ginger_tag(template=None, name=None, takes_context=False, mark_safe=False):
    def closure(orig_func):
        func = orig_func
        name_ = name or getattr(func,'_decorated_function',func).__name__
        if template:
            def wrapper(*args, **kwargs):
                from django.template import engines
                t = engines["GINGER"].get_template(template)
                values = orig_func(*args,**kwargs)
                result = t.render( values )
                result = jinja2.Markup(result)
                return result
            func = functools.update_wrapper(wrapper, func)
        elif mark_safe:
            def wrapper(*args, **kwargs):
                result = orig_func(*args, **kwargs)
                return jinja2.Markup(result)
            func = functools.update_wrapper(wrapper, func)
        if takes_context:
            func = jinja2.contextfunction(func)
        global_function(name_, func)
        return orig_func
    return closure


class MetaTemplateTag(type):
    def __init__(cls, *args, **kwargs):
        super(MetaTemplateTag, cls).__init__(*args, **kwargs)
        cls.register()


@six.add_metaclass(MetaTemplateTag)
class TemplateTag(object):

    template_name = None
    attribute_names = ()

    def __init__(self, **kwargs):
        super(TemplateTag, self).__init__()
        self.context = kwargs
        for attr in self.attribute_names:
            if hasattr(self, attr):
                raise TypeError("Invalid attribute: %r" % attr)
            setattr(self, attr, kwargs.get(attr))

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        return kwargs

    def render(self):
        from django.template import loader
        template_names = self.get_template_names()
        t = loader.select_template(template_names)
        context = self.get_context_data(**self.context)
        result = t.render(context)
        result = jinja2.Markup(result)
        return result

    @classmethod
    def register(cls, name=None, **init_kwargs):
        def wrapper(context, *args, **kwargs):
            ctx = init_kwargs.copy()
            ctx.update(context)
            ctx.update(kwargs)
            return cls(*args, **ctx).render()
        if name is None:
            name = camel_to_underscore(cls.__name__)
        global_function(name, jinja2.contextfunction(wrapper))
        return wrapper



function_tag = global_function

filter_tag = filter

test_tag = test
