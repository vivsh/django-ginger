
from django.utils.formats import localize
from .base import Formatter


class ChoiceFormatter(Formatter):

    def format(self, value, name, source):
        method = getattr(source, "get_%s_display" % name, None)
        if method:
            return method()
        return value


class DateTimeFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)


class DateFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)


class TimeFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)



