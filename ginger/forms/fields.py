
import mimetypes
import urllib2
from django.utils.encoding import force_text
from django.utils import six
import os
from urlparse import urlparse

from django import forms
from django.core.validators import URLValidator
from django.core.files.uploadedfile import SimpleUploadedFile
from ginger import ui, utils


__all__ = ["FileOrUrlInput", "HeightField", "HeightWidget", "SortField"]


class FileOrUrlInput(forms.ClearableFileInput):
    
    def extract_url(self, name, url):      
        validate = URLValidator()
        try:
            validate(url)
        except forms.ValidationError as _:
            raise
            return None
        
        parsed_url = urlparse(url)
        path = parsed_url[2].strip("/")
        name = os.path.basename(path)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        ze_file = opener.open(url).read()
        return SimpleUploadedFile(name=name, content=ze_file, content_type=mimetypes.guess_type(name))  

    def value_from_datadict(self, data, files, name):
        if name in files:
            return super(FileOrUrlInput, self).value_from_datadict(data,files,name)        
        else:
            url = forms.HiddenInput().value_from_datadict(data, files, name)
            result = self.extract_url(name, url) if url and isinstance(url, six.text_type) else None
            return result


class HeightWidget(forms.MultiWidget):

    def __init__(self, *args, **kwargs):
        widgets = [forms.TextInput(attrs={'placeholder': '5', 'size': '3'}), forms.TextInput(attrs={'placeholder': '6',
                                                                                                    'size': '3'})]
        super(HeightWidget,self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            v = int(value)
            inches = v/2.54
            return int(inches/12), int(inches%12)
        else:
            return [None,None]

    def format_output(self, rendered_widgets):
        return "%s ft   %s inches" % tuple(rendered_widgets)


class HeightField(forms.MultiValueField):
    widget = HeightWidget

    def __init__(self, *args, **kwargs):
        kwargs.pop('min_value',None)
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        reqd = kwargs.setdefault('required', False)
        fields = (
            forms.IntegerField(min_value=0,required=reqd),
            forms.IntegerField(min_value=0,required=reqd),
        )
        super(HeightField, self).__init__(fields, *args, **kwargs)

    def clean(self, value):
        result = super(HeightField,self).clean(value)
        return result

    def compress(self, data_list):
        if data_list and all(data_list):
            feet,inches = data_list
            return int((feet*12 + inches) * 2.54)
        return None


class SortField(forms.ChoiceField):

    def __init__(self, choices=(), toggle=True, *args, **kwargs):
        super(SortField, self).__init__(choices=choices, *args, **kwargs)
        self.toggle = toggle

    def valid_value(self, value):
        "Check to see if the provided value is a valid choice"
        text_value = force_text(value)
        if text_value.startswith("-"):
            text_value = text_value[1:]
        return super(SortField, self).valid_value(text_value)

    def build_links(self, request, bound_field):
        value = bound_field.value
        field_name = bound_field.name
        text_value = force_text(value) if value is not None else None
        for k, v in self.choices:
            content = force_text(v)
            key = force_text(k)
            is_active = text_value and text_value == key
            if is_active and self.toggle:
                next_value = key if text_value.startswith("-") else "-%s" % key
            else:
                next_value = key
            url = utils.get_url_with_modified_params(request, {field_name: next_value})
            yield ui.Link(url, content, is_active=is_active)

    def handle_queryset(self, queryset, value, bound_field):
        return queryset.order_by(value)


class DataSetSortField(SortField):

    def __init__(self, dataset_class, process_list=False, **kwargs):
        column_dict = dataset_class.get_column_dict()
        choices = [(name, col.label or name.title()) for name, col in six.iteritems(column_dict)]
        super(DataSetSortField, self).__init__(choices=choices, **kwargs)
        self.dataset_class = dataset_class
        self.process_list = process_list

    def handle_dataset(self, dataset, value, bound_field):
        text_value = force_text(value) if value is not None else None
        if not text_value:
            return
        reverse = text_value.startswith("-")
        name = text_value[1:] if reverse else text_value
        column = dataset.columns[name]
        column.sort(reverse=reverse)

