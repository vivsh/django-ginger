
import random
from django.db import models
from ginger.forms import HeightField as HeightFormField


__all__ = ['HeightField']


class HeightField(models.PositiveIntegerField):

    def formfield(self, **kwargs):
        defaults = {'form_class': HeightFormField}
        defaults.update(kwargs)
        return models.PositiveIntegerField.formfield(self, **defaults)

