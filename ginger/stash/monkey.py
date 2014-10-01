
from .compat import six
import inspect

class MonkeyProxy(object):
    
    def __init__(self, orig):
        self.orig_class = orig
        
    def __getattr__(self, name):
        return getattr(self.orig_class, name)


def patch_class(cls, mixin, methods=None):
    assert '_no_monkey' not in cls.__dict__, 'Multiple monkey mix not supported'
    cls._no_monkey = MonkeyProxy(cls)

    if methods is None:
        # NOTE: there no such thing as unbound method in Python 3, it uses naked functions,
        #       so we use some six based altering here
        isboundmethod = inspect.isfunction if six.PY3 else inspect.ismethod
        methods = inspect.getmembers(mixin, isboundmethod)
    else:
        methods = [(m, getattr(mixin, m)) for m in methods]

    for name, method in methods:
        if hasattr(cls, name):
            setattr(cls._no_monkey, name, getattr(cls, name))
        # NOTE: remember, there is no bound methods in Python 3
        setattr(cls, name, six.get_unbound_function(method))