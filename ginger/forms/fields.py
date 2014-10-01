
import mimetypes
import urllib2
import os
from urlparse import urlparse

from django import forms
from django.core.validators import URLValidator
from django.core.files.uploadedfile import SimpleUploadedFile


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
    


    