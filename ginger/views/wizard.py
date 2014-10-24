
import inspect
from django.core.urlresolvers import reverse
from django.http.response import Http404
from exceptions import ValidationFailure
from ginger.views.generic import GingerFormView

__all__ = ['Step', 'GingerWizardView']


class Step(object):

    container = None
    name = ""
    __position = 1

    def __init__(self, form_class=None, label=None, when=None, skip=False):
        Step.__position += 1
        self.__position = Step.__position
        self.form_class = form_class
        self.label = label
        self.when = when
        self.skip = skip

    @property
    def position(self):
        return self.__position


class BoundStep(object):

    def __init__(self, name, container, step):
        self.container = container
        self.step = step
        self.name = name

    @property
    def can_skip(self):
        return self.step.skip

    @property
    def name(self):
        return self.name

    @property
    def label(self):
        return self.step.label

    @property
    def wizard(self):
        return self.container.wizard

    def is_valid(self):
        result = True
        when = self.step.when
        if callable(when):
            result = when(self.wizard)
        elif when:
            result = getattr(self.wizard, when)()
        return True

    @property
    def is_active(self):
        return self.container.current == self

    @property
    def url(self):
        return self.wizard.get_step_url(self.name)

    def get_form_class(self):
        return self.form_class

    def is_first(self):
        return not self.has_previous()

    def is_last(self):
        return not self.has_next()

    def has_next(self):
        return self.container.has_next(self)

    def has_previous(self):
        return self.container.has_previous(self)


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
        self.items.sort(key=lambda a: a.step.position)

    def active_steps(self):
        for item in self.items:
            if item.is_valid():
                yield item

    def has_next(self, step):
        last = False
        for item in self.active_steps():
            if item == step:
                last = True
            elif last:
                last = False
        return last

    def has_previous(self, step):
        first = True
        for item in self.active_steps():
            if item == step and not first:
                return True
            first = False
        return False

    def all(self):
        return self.items[:]

    def find_name(self, step_name, invalid=False):
        for item in self.items:
            if invalid or item.is_valid():
                if item.name == step_name:
                    return item
        raise ValueError("Step %r not found" % step_name)

    @property
    def current(self):
        name = self.wizard.current_step_name
        return self.find_name(name, invalid=False)

    @property
    def first(self):
        return next(self.active_steps(), None)

    @property
    def last(self):
        last_step = None
        for step in self.active_steps():
            last_step = step
        return last_step

    @property
    def next(self):
        pass

    @property
    def previous(self):
        pass

    def __iter__(self):
        return self.active_steps()


class GingerWizardView(GingerFormView):

    done_step = "done"

    def __init__(self):
        super(GingerWizardView, self).__init__()
        self.steps = StepList(self)

    @property
    def current_step_name(self):
        return self.kwargs['step']

    def get_step_url(self, step_name):
        url_name = self.request.resolver_match.url_name
        kwargs = self.kwargs.copy()
        kwargs['step'] = step_name
        return reverse(url_name, args=self.args, kwargs=kwargs)

    def get_done_url(self):
        return self.get_step_url(self.done_step)

    def get_form_class_list(self):
        for form_class in self.steps:
            yield form_class

    def get_form_class(self):
        return self.steps.current.form_class

    def dispatch(self, request, *args, **kwargs):
        step_name = kwargs.get('step')
        self.current_step_name = step_name
        if step_name is None:
            return self.redirect(self.steps.first.url)
        if step_name == self.done_step and request.method == 'GET':
            return self.done(request, *args, **kwargs)
        if step_name not in self.steps:
            raise Http404
        return super(GingerWizardView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        data = request.GET
        form_class = self.steps.current.form_class
        if form_class.is_submitted(data):
            return self.process_form(form_class, data=data)
        else:
            return super(GingerWizardView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        step = self.steps.next
        if step is None:
            url = self.get_done_url()
        else:
            url = step.url
        return self.redirect(url)

    def serialize_form(self, form):
        pass

    def unserialize_form(self, form_class):
        pass

    def revalidate(self):
        pass

    def reset(self):
        pass

    def is_done(self):
        pass

    def mark_done(self):
        pass

    def done(self):
        if not self.is_done():
            try:
                self.revalidate()
            except ValidationFailure as ex:
                return self.form_invalid(ex.form)
            else:
                self.commit()
        self.mark_done()
        return self.render_done()

    def render_done(self):
        pass

    def commit(self):
        pass



