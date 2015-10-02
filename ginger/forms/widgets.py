
from django import forms


class EmptyWidget(forms.HiddenInput):
    """
    No html is produced. This is used for PageField
    """
    def render(self, name, value, attrs=None):
        return ""
