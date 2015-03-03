
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.files import File
import contextlib
import pytz.exceptions as pyex
import random
import importlib
from django.conf import settings
from django.contrib.gis.geos.point import Point
from django.db import models
from django.apps import apps
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict
from django.utils import timezone
from django.contrib.webdesign import lorem_ipsum as lipsum
from django.utils.functional import cached_property
from django.utils.text import camel_case_to_spaces
from . import utils
import datetime


__all__ = ['register', 'generate']


_processors = {}
_callback = None

def register(pretense, *models):
    if isinstance(pretense, type):
        pretense = pretense()
    for m in models:
        _processors[m] = pretense


def generate(model, n=20, name=None, callback=None):
    global _callback
    _callback = callback
    fac = Factory(model, limit=n, name=name)
    fac.create_all(n)


def on_create(ins):
    if _callback:
        _callback(model_to_dict(ins))


def boolean():
    return random.choice([True, False])


class IncompleteFactoryError(TypeError):
    pass


@contextlib.contextmanager
def impartial(obj):
    if obj.partial:
        raise IncompleteFactoryError
    obj.partial = True
    yield
    obj.partial = False


def get_file(conf_name, formats=None):
    folder = getattr(settings, conf_name)
    return utils.collect_files(folder, formats)


def get_image_file():
    conf_key = "GINGER_PRETENSE_IMAGE_DIRS"
    return utils.get_random_image(getattr(settings, conf_key))



class Field(object):

    def __init__(self, field, instance, index):
        self.field = field
        self.instance = instance
        self.index = index

    @property
    def null(self):
        return self.field.null

    @property
    def unique(self):
        return self.field.unique

    @property
    def choices(self):
        choices = getattr(self.field, 'choices', None)
        return list(choices) if choices else choices

    @property
    def primary_key(self):
        return self.field.primary_key

    @property
    def model(self):
        return self.field.rel.to

    @property
    def choice(self):
        return random.choice(self.choices)[0]

    def has_choices(self):
        return bool(self.choices)

    def __getattr__(self, item):
        return getattr(self.field, item)

    def set(self, value):
        if self.null and random.choice([True, False]):
            value = None
        setattr(self.instance, self.name, value)

    def __getattr__(self, item):
        return getattr(self.field, item)

    def __repr__(self):
        return "Field(%r)" % self.field


class Factory(object):

    __cache = {}
    __modules = None

    highest_id = 0
    total = 0

    def __new__(cls, model, limit=20, name=None):
        if model not in cls.__cache:
            obj = super(Factory, cls).__new__(cls)
            cls.__cache[model] = obj
            obj.model = model
            obj.meta = model._meta
            obj.fields = obj.meta.fields
            obj.total = obj.model.objects.count()
            obj.highest_id = obj.model.objects.order_by("id").last().id + 1 if obj.total else 0
            obj.partial = False
            obj.name = name
            Factory.load_pretenses()
        else:
            obj = cls.__cache[model]
        obj.limit = limit
        return obj

    @classmethod
    def load_pretenses(cls):
        if cls.__modules is None:
            cls.__modules = []
            for app in apps.get_app_configs():
                name = app.module.__name__
                module_name = "%s.pretenses" % name
                try:
                    mod = importlib.import_module(module_name)
                    cls.__modules.append(mod)
                except ImportError as ex:
                    pass

    @cached_property
    def processors(self):
        classes = [self.model] + list(self.model.__mro__)
        result = []
        if not self.name:
            for k in classes:
                if k not in _processors:
                    continue
                proc = _processors[k]
                result.append(proc)
        else:
            for mod in self.__modules:
                cls = getattr(mod, self.name, None)
                if cls is not None:
                    result.append(cls())
        result.append(DefaultProcessor(self))
        return result

    def post_save(self, ins):
        method_name = "after_%s_%s" % (self.meta.app_label, self.snake_case(self.model))
        for handler in self.processors:
            func = getattr(handler, method_name, None)
            if callable(func):
                func(ins, FactoryProxy)

    def find_method(self, field, default):
        for handler in self.processors:
            stream = getattr(handler, field.name, None)
            if stream:
                func = getattr(stream, 'next', None)
                if callable(func):
                    return func
            for name in self.method_names(field):
                func = getattr(handler, name, None)
                if callable(func):
                    return func
        return default

    @staticmethod
    def snake_case(cls):
        return camel_case_to_spaces(cls.__name__).lower().replace(" ", "_")

    def method_names(self, field):
        template = "process_%s"
        yield template % field.name
        yield template % self.snake_case(field.__class__)
        for cls in field.__class__.__mro__:
            if issubclass(cls, models.Field):
                yield template % self.snake_case(cls)

    def create(self, index, **kwargs):
        ins = self.model()
        for f in self.fields:
            field = Field(f, ins, index)
            name = field.name
            if name in kwargs:
                value = kwargs[name]
            else:
                if field.primary_key:
                    continue
                if field.has_choices():
                    value = field.choice
                else:
                    func = self.find_method(f, self.get_field_value)
                    value = func(field)
            if value is not None:
                field.set(value)
        ins.save()
        for f in self.meta.many_to_many:
            field = Field(f, ins, index)
            func = self.find_method(f, self.get_field_value)
            value = func(field)
            if value is not None:
                field.set(value)
        self.total += 1
        self.highest_id = ins.id
        self.post_save(ins)
        on_create(ins)
        return ins

    @cached_property
    def all(self):
        if self.limit >= self.total:
            self.create_all(self.limit-self.total)
        return list(self.model.objects.all())

    def get(self, index):
        i = index % len(self.all)
        return self.all[i]

    def create_all(self, limit=None, **kwargs):
        if limit is None:
            limit = self.limit
        i = 0
        errors = 0
        while i < limit:
            try:
                self.create(self.highest_id+i, **kwargs)
                i += 1
            except (IntegrityError, ValidationError, pyex.AmbiguousTimeError, pyex.NonExistentTimeError, pyex.InvalidTimeError) as ex:
                errors += 1
                if errors > limit * 5:
                    raise
            else:
                errors = 0

    def get_field_value(self, field):
        return None



class FactoryProxy(object):

    def __init__(self, model, limit=20):
        self.factory = Factory(model, limit)

    def create(self, limit=None, **kwargs):
        return self.factory.create_all(limit, **kwargs)


class DefaultProcessor(object):

    def __init__(self, factory):
        self.factory = factory

    def process_float_field(self, field):
        return random.uniform(0.1, 9999999999.28989)

    def process_decimal_field(self, field):
        limit = float("9"*field.max_digits)/10**field.decimal_places
        value = random.uniform(0.1, limit)
        return Decimal(value)

    def process_null_boolean_field(self, field):
        return boolean()

    def process_boolean_field(self, field):
        return boolean()

    def process_positive_small_integer_field(self, field):
        return random.randint(1, 32767)

    def process_positive_integer_field(self, field):
        return random.randint(1, 2147483647)

    def process_small_integer_field(self, field):
        return random.randint(-32767, 32767)

    def process_big_integer_field(self, field):
        return random.randint(0, 2147483647)

    def process_integer_field(self, field):
        return random.randint(-2147483647, 2147483647)

    def process_char_field(self, field):
        return lipsum.sentence()[: field.max_length]

    def process_text_field(self, field):
        limit = field.max_length
        para = lipsum.paragraphs(random.randint(2, 10), boolean())
        if limit:
            content = "\n".join(para)[: limit]
            para = content.splitlines(True)
        return "".join("<p>%s</p>" % p for p in para)

    def process_foreign_key(self, field):
        index = field.index
        factory = Factory(field.model)
        value = factory.get(index)
        return value

    def process_date_time_field(self, field):
        value = datetime.datetime.combine(self.process_date_field(field), self.process_time_field(field))
        return timezone.make_aware(value, timezone.get_default_timezone())

    def process_date_field(self, field):
        return datetime.date(year=random.randint(1970, 2015),
                             month=random.randint(1, 12),
                             day=random.randint(1, 28))

    def process_time_field(self, field):
        return datetime.time(hour=random.randint(0, 23), minute=random.randint(0,59), second=random.randint(0,59))

    def process_username(self, field):
        word = lipsum.words(1, False)
        return "%s%s" % (word, field.index)

    def process_ip_address_field(self, field):
        return ".".join(str(random.randint(1, 254)) for _ in range(4))

    def process_generic_ip_address_field(self, field):
        return self.process_ip_address_field(field)

    def process_json_field(self, field):
        return {}

    def process_password(self, field):
        word = lipsum.words(1, False)
        field.instance.set_password(word)

    def process_point_field(self, field):
        from geopy.distance import VincentyDistance
        km = random.randint(100, 1000)
        d = VincentyDistance(kilometers=km)
        latitude = random.randint(-179, 179)
        longitude = random.randint(-179, 179)
        bearing = random.randint(0, 359)
        p = d.destination((latitude, longitude),bearing)
        return Point(x=p.longitude, y=p.latitude)

    def process_image_field(self, field):
        filename = get_image_file()
        return File(open(filename))
