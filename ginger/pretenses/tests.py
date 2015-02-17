
from datetime import datetime, date, time
from .streams import *


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

def test_RandomPasswordStream():
    pwd = RandomPasswordStream(20, 5,100,100)
    print pwd.next(None)

def test_passwordstream():
    pwd = PasswordStream()
    print pwd.next(None)

def test_pointstream():
    p = PointStream(latitude=41.11, longitude=71.89)
    print p.next(None)







if __name__=="__main__":
    test_pointstream()

