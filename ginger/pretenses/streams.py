from decimal import Decimal
from datetime import datetime, timedelta, date, time
from IPython.external.path._path import path
from django.contrib.webdesign import lorem_ipsum as lorem
from django.utils.lru_cache import lru_cache
from django.core.files import File
from django.conf import settings
import random

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



class Paragraph(object):

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


class Integer(object):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def next(self, field):
        return random.randint(self.start,self.end)


class Sentence(object):

    def next(self, field):
        return lorem.sentence()


class FullName(object):

    def next(self, field):
        first_name = lorem.words(1, False)
        last_name = lorem.words(1, False)
        return "%s %s"%(first_name,last_name)


class FirstName(object):
    def next(self, field):
        return lorem.words(1,False)


class LastName(FirstName):
    def next(self, field):
        return lorem.words(1,False)


class DateTime(object):
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


class Date(DateTime):
    def __init__(self, start=None, end=None):
        if start is None:
            start = date(1900,1,1)
        if end is None:
            end = date.now()
        super(Date, self).__init__(datetime.combine(start, time()), datetime.combine(end, time()), False)

    def next(self, field):
        result = super(Date, self).next(field)
        return result.date()


class Time(DateTime):
    def __init__(self, start=None, end=None):
        if start is None:
            start = time(0, 0, 0)
        if end is None:
            end = time(23, 59, 59)
        if start > end:
            raise ValueError
        start = self.to_datetime(start)
        end = self.to_datetime(end)
        super(Time, self).__init__(start, end, False)

    @staticmethod
    def to_datetime(stamp):
        return datetime.combine(date.today(), stamp)

    def next(self, field):
        result = super(Time, self).next(field)
        return result.time()


class Float(Integer):
    def __init__(self, start, end):
        super(Float, self).__init__(start, end)

    def next(self, field):
        return random.uniform(0.1, 9999999999.28989)


class Words(object):
    def __init__(self, n=40):
        self.n = n

    def next(self, field):
        result = lorem.words(self.n, common=False)
        return result

#
class IPAddress(object):
    def next(self, field):
        return ".".join(str(random.randint(1, 254)) for _ in range(4))

class ImageField(object):
    def next(self, field):
        filename = random.choice(get_image_files())
        return File(open(filename))


class DecimalField(object):
    def next(self, field):
        limit = float("9"*field.max_digits)/10**field.decimal_places
        value = random.uniform(0.1, limit)
        return Decimal(value)

class Dummy:
    max_length = 10000
    max_digits = 10
    decimal_places=2

def test_name():
    n = FullName()
    print n.next(None)

def test_paragraph():
    p = Paragraph(1,5, html=True)
    for i in range(5):
        assert len(p.next(Dummy())) < 100, "Length is invalid"

def test_integer():
    i = Integer(3,500)
    print i.next(None)

def test_sentence():
    s = Sentence()
    print s.next(None)

def test_firstname():
    f = FirstName()
    print f.next(None)

def test_lastname():
    f = LastName()
    print f.next(None)

def test_datetime():
    d = DateTime(aware=False, start=datetime(2014, 5, 2), end=datetime(2015, 4, 2))
    print d.next(None)

def test_date():
    d = Date(start=date(2011, 5, 3), end=date(2015, 1, 1))
    print d.next(None)

def test_time():
    d = Time(start=time(1, 35, 0), end=time(23, 59, 59))
    print d.next(None)

def test_float():
    f = Float(start=1, end=99)
    print f.next(None)

def test_words():
    w = Words()
    print w.next(None)

def test_ipaddress():
    ip = IPAddress()
    print ip.next(None)

def test_imagefield():
    img = ImageField()
    print img.next(None)

def test_decimalfield():
    dec = DecimalField()
    print dec.next(Dummy)


if __name__=="__main__":
    test_float()