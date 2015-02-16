from decimal import Decimal
from datetime import datetime, timedelta, date, time
from os import path
from django.contrib.webdesign import lorem_ipsum as lorem
from django.utils.lru_cache import lru_cache
from django.core.files import File
from django.conf import settings
from django.contrib.gis.geos.point import Point
import random


__all__= [
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
    "PasswordRandomStream",
    "PasswordStream",
    "ParagraphStream",
    "SentenceStream",
    "IPAddressStream",
    "ImageStream",
    "PointStream",
    "ChoiceStream"
          ]


_images = None


def get_image_files():
    return get_files("GINGER_PRETENSE_IMAGE_DIRS", ("jpg", "png", "gif", "jpeg", "bmp", "tiff", "pnga"))

@lru_cache(maxsize=16)
def get_files(conf_name, formats=None):
    global _images
    if _images is not None:
        return _images
    folder = getattr(settings, conf_name)
    _images = []
    return collect_files(folder, formats)

def process_image_field(self, field):
        filename = random.choice(get_image_files())
        return File(open(filename))

def collect_files(folders, extensions=None):
    _images = []
    if not isinstance(folders, (tuple, list)):
        folders = (folders, )
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for f in files:
                _, ext = path.splitext(f)
                ext = ext.strip(".").lower()
                if extensions is None or ext in extensions:
                    filename = path.join(root, f)
                    _images.append(filename)
    return _images



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


class IntegerStream(object):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def next(self, field):
        return random.randint(self.start,self.end)


class SentenceStream(object):

    def next(self, field):
        return lorem.sentence()


class FullNameStream(object):

    def next(self, field):
        first_name = lorem.words(1, False)
        last_name = lorem.words(1, False)
        return "%s %s"%(first_name,last_name)


class FirstNameStream(object):
    def next(self, field):
        return lorem.words(1,False)


class LastNameStream(FirstNameStream):
    def next(self, field):
        return lorem.words(1,False)


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
            start = date(1900,1,1)
        if end is None:
            end = date.now()
        super(DateStream, self).__init__(datetime.combine(start, time()), datetime.combine(end, time()), False)

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
        start = self.to_datetime(start)
        end = self.to_datetime(end)
        super(TimeStream, self).__init__(start, end, False)

    @staticmethod
    def to_datetime(stamp):
        return datetime.combine(date.today(), stamp)

    def next(self, field):
        result = super(TimeStream, self).next(field)
        return result.time()


class FloatStream(IntegerStream):
    def __init__(self, start, end):
        super(FloatStream, self).__init__(start, end)

    def next(self, field):
        return random.uniform(0.1, 9999999999.28989)


class WordStream(object):
    def __init__(self, n=4):
        self.n = n

    def next(self, field):
        result = lorem.words(self.n, common=False)
        return result

#
class IPAddressStream(object):
    def next(self, field):
        return ".".join(str(random.randint(1, 254)) for _ in range(4))

class ImageStream(object):
    def __init__(self, path):
        self.path = path

    def next(self, field):
        filename = random.choice(collect_files(self.path, ("jpg", "png", "gif", "jpeg", "bmp", "tiff", "pnga")))
        return File(open(filename))


class DecimalStream(object):
    def next(self, field):
        limit = float("9"*field.max_digits)/10**field.decimal_places
        value = random.uniform(0.1, limit)
        return Decimal(value)


class PasswordStream(object):
    def __init__(self, word):
        self.word = word

    def next(self, field):
        from django.contrib.auth.hashers import make_password
        return make_password(self.word)


class PasswordRandomStream(object):
    def __init__(self, max_length=32, min_length=1, specials=1, capitals = 1):
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
        if self.longitude is None:
            self.longitude = random.randint(-179, 179)
        if self.latitude is None:
            self.latitude = random.randint(-179, 179)
        if self.radius is None:
            self.radius = random.randint(100, 1000)
        from geopy.distance import VincentyDistance
        m = random.randint(100, 1000)
        d = VincentyDistance(meters=m)
        bearing = random.randint(0, 359)
        p = d.destination((self.latitude, self.longitude),bearing)
        return Point(x=p.longitude, y=p.latitude)

class Dummy:
    max_length = 10000
    max_digits = 10
    decimal_places=2


def test_name():
    n = FullNameStream()
    print n.next(None)

def test_paragraph():
    p = ParagraphStream(1,5, html=True)
    for i in range(5):
        assert len(p.next(Dummy())) < 100, "Length is invalid"

def test_integer():
    i = IntegerStream(3,500)
    print i.next(None)

def test_sentence():
    s = SentenceStream()
    print s.next(None)

def test_firstname():
    f = FirstNameStream()
    print f.next(None)

def test_lastname():
    f = LastNameStream()
    print f.next(None)

def test_datetime():
    d = DateTimeStream(aware=False, start=datetime(2014, 5, 2), end=datetime(2015, 4, 2))
    print d.next(None)

def test_date():
    d = DateStream(start=date(2011, 5, 3), end=date(2015, 1, 1))
    print d.next(None)

def test_time():
    d = TimeStream(start=time(1, 35, 0), end=time(23, 59, 59))
    print d.next(None)

def test_float():
    f = FloatStream(start=1, end=99)
    print f.next(None)

def test_words():
    w = WordStream()
    print w.next(None)

def test_ipaddress():
    ip = IPAddressStream()
    print ip.next(None)

def test_imagestream():
    img = ImageStream()
    print img.next(None)

def test_decimalstream():
    dec = DecimalStream()
    print dec.next(Dummy)

def test_passwordrandomstream():
    pwd = PasswordRandomStream(20, 5,100,100)
    print pwd.next(None)

def test_passwordstream():
    pwd = PasswordStream()
    print pwd.next(None)

def test_pointstream():
    p = PointStream(latitude=41.11, longitude=71.89)
    print p.next(None)







if __name__=="__main__":
    test_pointstream()
