from django import forms


class ActionFormMixin(object):

    def __init__(self, *args, **kwargs):
        super(ActionFormMixin, self).__init__(*args, **kwargs)

    def add_field(self, name, field):
        pass

    def remove_field(self, name):
        pass

    def execute(self, method):
        pass

    def render(self):
        return


class ActionForm(ActionFormMixin, forms.Form):
    pass


class ObjectForm(ActionFormMixin, forms.ModelForm):

    def create(self):
        self.save()

    def update(self):
        self.save()


def filter_factory_callback(f, **kwargs):
    return



class FilterForm(forms.ModelForm):

    formfield_callback = filter_factory_callback

    def filter(self):
        queryset = self.queryset

        return

    def save(self, commit=True):
        raise NotImplementedError