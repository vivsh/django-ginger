from django import forms
from ginger.staging import conf


class StagingForm(forms.Form):
    
    secret = forms.CharField(max_length=128)
    
    def clean_secret(self):
        value = self.cleaned_data['secret']
        if value != conf.STAGING_SECRET:
            raise forms.ValidationError("Oops! you have entered an invalid secret. Please try again")
        return value