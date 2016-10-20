
from django.utils.formats import localize
from .base import Formatter


class ChoiceFormatter(Formatter):

    def format(self, value, name, source):
        return getattr(source, "get_%s_display" % name)()


class DateTimeFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)


class DateFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)


class TimeFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)



