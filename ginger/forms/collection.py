
from django import forms
from ginger.forms.actions import GingerModelForm


__all__ = ['FormCollection', 'FormCollectionItem']


class FormCollection(object):

    def __init__(self, form, form_class, name=None, limit=10, extra=4):
        self.limit = limit
        self.form_class = form_class
        self.form = form
        self.name = name or form_class.__name__.lower()
        self.forms = []
        self.extra = extra

    def create_all(self, instances):
        for en in instances:
            self.create(en)
        for i in xrange(self.extra):
            self.create()

    def create(self, instance=None):
        context = self.form.context.copy()
        prefix = "%s__%s" % (self.name, len(self.forms))
        kwargs = dict(
                    data=self.form.data if self.form.is_bound else None,
                    files=self.form.files if self.form.is_bound else None,
                    prefix=prefix,
                    instance=instance,
                    parent=getattr(self.form, 'instance', None),
                    **context
        )
        form = self.form_class(**kwargs)
        self.forms.append(form)

    def clean(self):
        errors = {}
        for form in self.forms:
            if not form.is_valid():
                errors[form.prefix] = form.errors.values()
        if errors:
            raise forms.ValidationError(errors)

    def save(self):
        for form in self.forms:
            if form.is_valid():
                form.run()
        limit = self.limit
        while limit:
            self.create()
            form = self.forms.pop(-1)
            if not form.is_valid():
                break
            else:
                form.save()
            limit -= 1


class FormCollectionItem(GingerModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def __init__(self, **kwargs):
        super(FormCollectionItem, self).__init__(**kwargs)
        id_ = self.instance.id
        if id_:
            self.initial['id'] = id_

    def clean(self):
        result = super(FormCollectionItem, self).clean()
        if not self.is_new() and self.instance.id != self.cleaned_data['id']:
                raise forms.ValidationError({"id": "Invalid id value"})
        return result

    def is_new(self):
        return self.instance.id is None

