import functools
import jinja2


__all__ = ['function_tag', 'filter_tag', 'test_tag', 'ginger_tag']


_env = None


def get_env():
    global _env
    if _env is None:
        from django.template import engines
        _env = engines["GINGER"].env
    return _env


def _attach_function(attr, func, name=None):
    if name is None:
        name = func.__name__
    env = get_env()
    getattr(env, attr)[name] = func
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


function_tag = global_function

filter_tag = filter

test_tag = test
