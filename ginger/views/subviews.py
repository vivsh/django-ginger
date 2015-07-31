
from copy import deepcopy
from ginger.views import GingerView


class SubView(object):
    pass


if __name__ == '__main__':
    cls = deepcopy(GingerView)
    print cls, cls.__module__, cls.meta == GingerView.meta
