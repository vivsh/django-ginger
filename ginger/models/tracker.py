
import weakref
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_init, post_save


class FieldTracker(object):

    def __init__(self, model, field_names):
        self.model = weakref.ref(model)
        self.field_names = set(field_names)
        self.data = {}
        self.reset()

    def __getstate__(self):
        data = self.__dict__.copy()
        data['model'] = None
        return data

    def is_dirty(self):
        return any(self.has_changed(f) for f in self.field_names)

    def reset(self):
        self.clear()
        for f in self.field_names:
            self.data[f] = getattr(self.model(), f)

    def clear(self):
        self.data.clear()

    def has_changed(self, field_name):
        return field_name in self.field_names and self.data.get(field_name) != getattr(self.model(), field_name)

    def changed_data(self):
        return {k: self.data.get(k) for k in self.field_names if self.has_changed(k)}


class FieldTrackerDescriptor(object):

    def __init__(self, field_names):
        super(FieldTrackerDescriptor, self).__init__()
        self.field_names = field_names

    def __get__(self, instance, owner):
        if instance is None:
            raise ImproperlyConfigured("Tracker only works on instances")
        try:
            result = instance.__field_tracker
            if result.model is None:
                result.model = weakref.ref(instance)
        except AttributeError:
            result = FieldTracker(instance, self.field_names)
            instance.__field_tracker = result
        return result


def on_init(sender, instance, **kwargs):
    tracker = getattr(sender,"_tracking_attr")
    getattr(instance, tracker).reset()


def on_save(sender, instance, **kwargs):
    tracker = getattr(sender,"_tracking_attr")
    getattr(instance, tracker).reset()


def setup_tracker(model, attr, fields):
    model._tracking_attr = attr
    setattr(model, attr, FieldTrackerDescriptor(fields))
    post_init.connect(on_init, model)
    post_save.connect(on_save, model)


def track_fields(fields, attr="tracker"):
    def wrapper(model):
        setup_tracker(model, attr, fields)
        return model
    return wrapper

