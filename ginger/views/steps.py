

import inspect
from django import forms
from django.core.exceptions import ImproperlyConfigured

from ginger.forms import GingerForm


__all__ = ['Step', 'StepList']


class DummyStepForm(GingerForm):

    errors = {}
    cleaned_data = {}

    def is_valid(self):
        return True


class Step(object):

    container = None
    name = ""
    __position = 1

    def __init__(self, form=DummyStepForm, label=None, when=None, skip=False, method="POST", template=None):
        form_class = form
        Step.__position += 1
        self.__position = Step.__position
        self.form_class = form_class
        self.label = label
        self.when = when
        self.skip = skip
        self.method = method.upper()
        self.template = template
        if not isinstance(form_class, type) or not issubclass(form_class, (forms.Form, forms.ModelForm)):
            raise ImproperlyConfigured("%r is not a valid form class for wizard steps" % form_class)

    @property
    def position(self):
        return self.__position


class BoundStep(object):

    def __init__(self, name, step, container):
        self.container = container
        self.step = step
        self._name = name

    @property
    def can_skip(self):
        return self.step.skip

    @property
    def name(self):
        return self._name

    @property
    def position(self):
        return self.step.position

    @property
    def label(self):
        return self.step.label

    @property
    def template(self):
        return self.step.template

    @property
    def method(self):
        return self.step.method

    @property
    def wizard(self):
        return self.container.wizard

    def is_enabled(self):
        result = True
        when = self.step.when
        if callable(when):
            result = when(self.wizard)
        elif when:
            result = getattr(self.wizard, when)()
        return bool(result)

    @property
    def has_form(self):
        return self.get_form_class() is None

    @property
    def is_active(self):
        return self.container.current == self

    @property
    def url(self):
        return self.wizard.get_step_url(self.name)

    def get_form_class(self):
        return self.step.form_class

    def is_first(self):
        return not self.has_previous()

    def is_last(self):
        return not self.has_next()

    def has_next(self):
        return self.container.has_next(self)

    def has_previous(self):
        return self.container.has_previous(self)

    def next(self):
        return self.container.next_step(self)

    def previous(self):
        return self.container.previous_step(self)

    def __repr__(self):
        return "<BoundStep: %s>" % self.name


class StepList(object):

    def __init__(self, wizard):
        self.wizard = wizard
        self.items = []
        self._load_steps()

    def _load_steps(self):
        for name, value in inspect.getmembers(self.wizard):
            if isinstance(value, Step):
                item = BoundStep(name, value, self)
                self.items.append(item)
        self.items.sort(key=lambda a: a.position)
        if not self.items:
            raise ImproperlyConfigured("StepList has to have atleast one step")

    def enabled_steps(self):
        result = []
        for item in self.items:
            if item.is_enabled():
                result.append(item)
        return result

    def has_next(self, step):
        steps = self.enabled_steps()
        return steps[-1] != step

    def has_previous(self, step):
        steps = self.enabled_steps()
        return steps[0] != step

    def all(self):
        return self.items[:]

    def find_name(self, step_name, enabled=True):
        for item in self.items:
            if not enabled or item.is_enabled():
                if item.name == step_name:
                    return item
        raise ValueError("Step %r not found" % step_name)

    def names(self):
        return [step.name for step in self]

    @property
    def current(self):
        name = self.wizard.current_step_name()
        return self.find_name(name, enabled=True)

    @property
    def first(self):
        steps = self.enabled_steps()
        return steps[0]

    @property
    def last(self):
        steps = self.enabled_steps()
        return steps[-1]

    @property
    def next(self):
        return self.current.next

    @property
    def previous(self):
        return self.current.previous

    def next_step(self, step):
        steps = self.enabled_steps()
        size = len(steps)
        for i, item in enumerate(steps):
            if step == item and i < size-1:
                return steps[i+1]

    def previous_step(self, step):
        steps = self.enabled_steps()
        for i, item in enumerate(steps):
            if step == item and i > 0:
                return steps[i-1]

    def __iter__(self):
        return iter(self.enabled_steps())

    def __len__(self):
        return len(self.enabled_steps())

    def __getitem__(self, step_name):
        return self.find_name(step_name, enabled=True)

