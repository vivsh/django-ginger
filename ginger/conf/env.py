
import os
import ast
import re

__all__ = ['get']


_cache = None


def get_cache():
    global _cache
    if _cache is None:
        _cache = {}
        _update(os.environ)
        try:
            env_file = os.path.abspath(os.path.join(os.environ['VIRTUAL_ENV'], "../.env"))
        except KeyError:
            pass
        else:
            if os.path.exists(env_file):
                load_file(env_file)
    return _cache


def _set(key, value):
    _cache[key] = value


def _update(values):
    for key in values:
        _set(key, values[key])


def load_file(path):
    result = {}
    with open(path) as fh:
        content = fh.read()
        for line in content.splitlines():
            values = re.findall(r'\s*(\w+)\s*=\s*(.+)\s*', line)
            if values:
                key, value = values[0]
                result[key]= value.strip()
    _update(result)


def get(key, default=None):
    cache = get_cache()
    return cache.get(key, default)


def all():
    cache = get_cache()
    return cache.copy()
