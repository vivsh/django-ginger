
import functools


def make_cache_key(*args, **kwargs):
    return

def make_invalidator(func):
    def actor(*args, **kwargs):
        cache_key = ""
    return actor

def cache_html(timeout, template):
    def closure(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = "" 
            ctx = func(*args, **kwargs)
        return wrapper
        wrapper.invalidate = make_invalidator(wrapper)
    return closure