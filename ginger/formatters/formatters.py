
from django.utils.formats import localize
from .base import Formatter


class ChoiceFormatter(Formatter):

    def format(self, value, name, source):
        return getattr(source, "get_%s_display" % name)()



class FileFormatter(Formatter):

    def __init__(self, **kwargs):
        kwargs.setdefault("variants", "detail")
        super(FileFormatter, self).__init__(**kwargs)

    def format(self, value, name, source):
        if not value:
            return ""
        obj = getattr(source, name)
        url = obj.url
        name = obj.name
        tag = "<a href='%s'>%s</a>" % (url, name)
        return tag


class ImageFormatter(Formatter):

    def __init__(self, **kwargs):
        self.width = kwargs.pop("width", 48)
        self.height = kwargs.pop("height", 48)
        kwargs.setdefault("variants", "detail")
        super(ImageFormatter, self).__init__(**kwargs)

    def format(self, value, name, source):
        if not value:
            return ""
        url = getattr(source, name).url
        tag = "<img src='%s' width='%s' height='%s' >" % (url, self.width, self.height)
        return tag


class DateTimeFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)


class DateFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)


class TimeFormatter(Formatter):

    def format(self, value, name, source):
        return localize(value)



