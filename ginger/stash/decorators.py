from __future__ import division
import inspect
import functools
import random

from django.core import cache

from . import utils
from django.template.loader import render_to_string


def set_invalidator(wrapper, backend, name, prefix):
    
    def func(*args, **kwargs):
        store = cache.get_cache(backend)
        cache_key = utils.get_cache_key(name, *args, **kwargs)
        if prefix:
            cache_key = "%s:%s"%(prefix, cache_key)
        store.delete(cache_key)
        
    def func_many(params):
        store = cache.get_cache(backend)
        key_list = []
        for args, kwargs in params:
            cache_key = utils.get_cache_key(name, *args, **kwargs)
            if prefix:
                cache_key = "%s:%s"%(prefix, cache_key)
            key_list.append(cache_key)
        store.delete_many(key_list)
        
    wrapper.invalidate = func
    
    wrapper.invalidate_many = func_many


def cached(timeout=60*60, backend="default", template=None, prefix=None, method=False, noise=5):
    def closure(func):
        backend_ = cache.get_cache(backend)
        name = "%s.%s"%(inspect.getsourcefile(func), func.__name__)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if method:
                params = args[1:]
            else:
                params = args
            cache_key = utils.get_cache_key(name, *params, **kwargs)
            if prefix:
                cache_key = "%s:%s"%(prefix, cache_key)
            result = backend_.get(cache_key)
            if not result:
                result = func(*args, **kwargs)
                if template:
                    result = render_to_string(template, result)
                ttl = random.randint( int(timeout * ((100-noise)/100)), int(timeout * ((100+noise)/100)) )
                backend_.set(cache_key, result, ttl)
            return result
        set_invalidator(wrapper, backend, name, prefix)
        return wrapper
    return closure


            