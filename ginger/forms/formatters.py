from collections import defaultdict

registry = defaultdict(dict)


def register(model_class, **kwargs):
    return


class Column(object):
    pass


class Second(object):

    def format(self, value, **context):
        return


class Dollar(object):

    def format(self):
        pass


class Delegate(object):

    def format(self, value, name, row):
        return

class Generic(object):
    pass