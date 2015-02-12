
import contextlib
import random
import importlib
from django.db import models
from django.apps import apps
from django.utils import six
from django.contrib.webdesign import lorem_ipsum as lipsum
from django.utils.functional import cached_property
from django.utils.text import camel_case_to_spaces


__all__ = ['register']


_processors = {}


def register(pretense, *models):
    for m in models:
        _processors[m] = pretense

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

    highest_id = 0
    total = 0

    def __new__(cls, model, limit=20, *args, **kwargs):
        if model not in cls.__cache:
            obj = super(Factory, cls).__new__(cls)
            cls.__cache[model] = obj
            obj.model = model
            obj.meta = model._meta
            obj.fields = obj.meta.fields
            obj.total = obj.model.objects.count()
            obj.highest_id = obj.model.objects.order_by("id").last().id if obj.total else 0
            obj.partial = False
            app = apps.get_app_config(obj.meta.app_label)
            name = app.module.__name__
            try:
                importlib.import_module("%s.pretenses" % name)
            except ImportError:
                pass
        else:
            obj = cls.__cache[model]
        obj.limit = limit
        return obj

    @cached_property
    def processors(self):
        classes = [self.model] + list(self.model.__mro__)
        result = []
        for k in _processors:
            if k in classes:
                result.append(k)
        result.sort(key=lambda a: classes.index(a), reverse=True)
        result.append(self)
        return result

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
        for cls in field.__class__.mro():
            if issubclass(cls, models.Field):
                yield template % self.snake_case(cls)

    def create(self, index):
        ins = self.model()
        for f in self.fields:
            field = Field(f, ins, index)
            if field.primary_key:
                continue
            if field.has_choices():
                value = f.choice
            else:
                func = self.find_method(f, self.get_field_value)
                value = func(field)
            if value is not None:
                field.set(value)
        ins.save()
        self.total += 1
        self.highest_id = ins.id
        return ins

    @cached_property
    def all(self):
        if self.limit < self.total:
            self.create_all(self.limit-self.total)
        return list(self.model.objects.all())

    def get(self, index):
        i = index % len(self.all)
        return self.all[i]

    def create_all(self, limit=20):
        for i in six.moves.range(limit):
            self.create(self.highest_id+i)

    def get_field_value(self, field):
        return None

    def process_boolean_field(self, field):
        return boolean()

    def process_positive_small_integer_field(self, field):
        return random.randint(1, 127)

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
        factory = Factory(field.model, self.limit)
        value = factory.get(index)
        return value

    def process_date_time_field(self, field):
        return

    def process_date_field(self):
        return

    def process_point_field(self):
        return
