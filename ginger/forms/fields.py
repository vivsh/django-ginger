
import mimetypes
import urllib2
import os
from urlparse import urlparse

from django import forms
from django.core.validators import URLValidator
from django.core.files.uploadedfile import SimpleUploadedFile

__all__ = ["FileOrUrlInput", "HeightField", "HeightWidget"]

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
            result = self.extract_url(name, url) if url else None
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
