
from decimal import Decimal
from datetime import datetime, timedelta, date, time
from django.contrib.webdesign import lorem_ipsum as lorem
from django.core.files import File
from django.contrib.gis.geos.point import Point
import random

from . import utils


__all__ = [
    "IntegerStream",
    "FloatStream",
    "DateTimeStream",
    "DateStream",
    "TimeStream",
    "DecimalStream",
    "WordStream",
    "FirstNameStream",
    "LastNameStream",
    "FullNameStream",
    "RandomPasswordStream",
    "PasswordStream",
    "ParagraphStream",
    "SentenceStream",
    "IPAddressStream",
    "PointStream",
    "ChoiceStream",
    "ImageStream",
    "FileStream",
    "ForeignKeyStream",
    "OneToOneStream",
    "ManyToManyStream"
]


class IntegerStream(object):

    def __init__(self, start=0, end=255):
        self.start = start
        self.end = end

    def next(self, field):
        return random.randint(self.start, self.end)


class FloatStream(IntegerStream):

    def __init__(self, start, end):
        super(FloatStream, self).__init__(start, end)

    def next(self, field):
        return random.uniform(0.000001, 9999999999.99999999)


class WordStream(object):

    def __init__(self, n=4):
        self.n = n

    def next(self, field):
        result = lorem.words(self.n, common=False)
        return result


class SentenceStream(object):

    def next(self, field):
        return lorem.sentence()


class ParagraphStream(object):

    def __init__(self, minimum=1, maximum=10, html=False):
        self.minimum = minimum
        self.maximum = maximum
        self.html = html

    def next(self, field):
        limit = random.randint(self.minimum,self.maximum)
        result = "\n".join(lorem.paragraphs(limit))
        if field.max_length:
            result = result[:field.max_length]
        if self.html:
            html_result = []
            for item in result.splitlines(True):
                html_result.append('<p>'+item+'</p>')
            return ''.join(html_result)
        return result


class FullNameStream(object):

    def next(self, field):
        first_name = lorem.words(1, False)
        last_name = lorem.words(1, False)
        return "%s %s" % (first_name,last_name)


class FirstNameStream(object):

    def next(self, field):
        return lorem.words(1,False)


class LastNameStream(FirstNameStream):
    pass


class DateTimeStream(object):

    def __init__(self, start=None, end=None, aware=True):
        if start is None:
            start = datetime(1900, 1, 1)
        if end is None:
            end = datetime.now()
        if end < start:
            raise ValueError("End %s can't be less than start %s" % (end, start))
        self.start = start
        self.end = end
        self.aware = aware

    def next(self, field):
        delta = (self.end-self.start).total_seconds()
        interval = random.randint(1, int(delta))
        result = self.start + timedelta(seconds=interval)
        if self.aware:
            from django.utils import timezone
            timezone.make_aware(result, timezone.get_default_timezone())
        return result


class DateStream(DateTimeStream):

    def __init__(self, start=None, end=None):
        if start is None:
            start = date(1900, 1, 1)
        if end is None:
            end = date.now()
        super(DateStream, self).__init__(datetime.combine(start, time()),
                                            datetime.combine(end, time()), False)

    def next(self, field):
        result = super(DateStream, self).next(field)
        return result.date()


class TimeStream(DateTimeStream):

    def __init__(self, start=None, end=None):
        if start is None:
            start = time(0, 0, 0)
        if end is None:
            end = time(23, 59, 59)
        if start > end:
            raise ValueError
        start, end = map(self.to_datetime, (start, end))
        super(TimeStream, self).__init__(start, end, False)

    @staticmethod
    def to_datetime(stamp):
        return datetime.combine(date.today(), stamp)

    def next(self, field):
        result = super(TimeStream, self).next(field)
        return result.time()


class IPAddressStream(object):

    def next(self, field):
        return ".".join(str(random.randint(1, 254)) for _ in range(4))


class ImageStream(object):
    def __init__(self, paths):
        self.folder = paths

    def next(self, field):
        filename = utils.get_random_image(self.folder)
        return File(open(filename))


class FileStream(object):
    
    def __init__(self, paths, extensions=None):
        self.folders = paths
        self.extensions = extensions

    def next(self, field):
        filename = utils.get_random_file(self.folders, self.extensions)
        return File(open(filename))


class DecimalStream(object):

    def __init__(self, start=None, end=None):
        if start is None:
            start = 0.0
        if end is None:
            end = 9999999999.999999
        self.start = int(start)
        self.end = int(end)

    def next(self, field):
        value = random.randint(self.start, self.end)
        value = str(value)[:field.max_digits]
        return Decimal(value)/10**field.decimal_places


class PasswordStream(object):

    def __init__(self, word):
        from django.contrib.auth.hashers import make_password
        self.word = word
        self.hash_code = make_password(self.word)

    def next(self, field):
        return self.hash_code


class RandomPasswordStream(object):

    def __init__(self, max_length=32, min_length=1, specials=1, capitals=1):
        self.max_length = max_length
        self.min_length = min_length
        self.specials = specials
        self.capitals = capitals
        if max_length < min_length:
            raise ValueError("max length should be greater than min length")

    def next(self, field):
        list_special_char = ['!','@','#','$','%','^','&','*','(',')','+','_','~','<','>','|','{','}','[',']','`']
        password = ""
        size = random.randint(self.min_length, self.max_length)
        while len(password) <  size:
            password += lorem.words(1, common=False)
        password = password[:size]
        result = list(password)
        positions = set(range(len(password)))

        specials = self.specials % size
        special_positions = random.sample(range(len(password)), specials)
        positions.difference_update(special_positions)

        for i in special_positions:
            result[i] = random.choice(list_special_char)

        capitals = self.capitals % len(positions)
        for i in random.sample(positions, capitals):
            result[i] = result[i].upper()

        return "".join(result)


class ChoiceStream(object):
    def __init__(self, choices):
        self.choices = choices

    def next(self, field):
        return random.choice(self.choices)


class PointStream(object):
    def __init__(self, longitude=None, latitude=None, radius=None):
        self.longitude = longitude
        self.latitude = latitude
        self.radius = radius

    def next(self, field):
        from geopy.distance import VincentyDistance
        longitude = random.randint(-179, 179) if self.longitude is None else self.longitude
        latitude = random.randint(-179, 179) if self.latitude is None else self.latitude
        radius = random.randint(100, 6000) if self.radius is None else self.radius
        d = VincentyDistance(kilometers=radius)
        bearing = random.randint(0, 359)
        p = d.destination((latitude, longitude), bearing)
        return Point(x=p.longitude, y=p.latitude)


class ForeignKeyStream(object):
    def __init__(self, queryset):
        self.queryset = queryset
        self.total = len(self.queryset)

    def next(self, field):
        i = random.randint(0, self.total-1)
        return self.queryset[i]


class OneToOneStream(ForeignKeyStream):
    pass


class ManyToManyStream(object):
    def __init__(self, queryset, limit=None):
        self.queryset = queryset
        self.total = len(self.queryset)
        self.limit = limit

    def next(self, field):
        size = self.limit if self.limit is not None else random.randint(0, self.total-1)
        i = random.randint(0, self.total-1)
        items = self.queryset[i: i+size]
        return items
