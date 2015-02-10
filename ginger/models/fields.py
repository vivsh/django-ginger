

from django.db import models
from ginger.forms import HeightField as HeightFormField
from django.db.models import ImageField, signals
from django.db.models.fields.files import ImageFieldFile, ImageFileDescriptor
from django.core.files.base import ContentFile
import os
from StringIO import StringIO


__all__ = ['HeightField', "GingerImageField", "GingerImageFileDescriptor", "GingerImageFieldFile"]



class HeightField(models.PositiveIntegerField):

    def formfield(self, **kwargs):
        defaults = {'form_class': HeightFormField}
        defaults.update(kwargs)
        return models.PositiveIntegerField.formfield(self, **defaults)


class GingerImageFileDescriptor(ImageFileDescriptor):

    def __set__(self, instance, value):
        name = self.field.name
        old_value = None
        if name in instance.__dict__:
            old_value = getattr(instance, name)
        if old_value and old_value != value:
            old_value.delete(False)
        result = super(GingerImageFileDescriptor, self).__set__(instance, value)
        self.field.set_variations(instance)
        return result


class GingerImageFieldFile(ImageFieldFile):

    def save(self, name, content, save=True):
        result = super(GingerImageFieldFile, self).save(name, content, save)

        for variation in self.field.variations:
            self.render_and_save_variation(name, content, variation)
        return result

    def render_and_save_variation(self, name, content, variation):
        """
        Renders the image variations and saves them to the storage
        """
        spec = variation['spec']
        content.seek(0)
        file_buffer = spec(source=content.file).generate()
        variation_name = self.get_variation_name(self, variation)
        self.storage.save(variation_name, ContentFile(file_buffer.getvalue()))
        file_buffer.close()

    @classmethod
    def get_variation_name(cls, field, variation):
        """
        Returns the variation file name based on the model it's field and it's variation
        """
        name = field.name
        head, tail = os.path.split(name)
        file_name, ext = os.path.splitext(tail)
        path = head
        if not ext:
            ext = ".jpg"
        return os.path.join(path, '%s.%s%s' % (file_name, variation['name'], ext))

    def delete(self, save=True):
        for variation in self.field.variations:
            field = getattr(self.instance, self.field.name)
            if field:
                variation_name = self.get_variation_name(field, variation)
                self.storage.delete(variation_name)

        super(GingerImageFieldFile, self).delete(save)


class GingerImageField(ImageField):

    attr_class = GingerImageFieldFile
    descriptor_class = GingerImageFileDescriptor

    def __init__(self, verbose_name=None, name=None, variations={}, *args, **kwargs):

        self.variations = []

        for key, attr in variations.iteritems():
            self.variations.append({'name': key, 'spec': attr})
            setattr(self, key, attr)

        super(GingerImageField, self).__init__(verbose_name, name, *args, **kwargs)


    def set_variations(self, instance=None, **kwargs):
        """
        Creates a "variation" object as attribute of the ImageField instance.
        Variation attribute will be of the same class as the original image, so
        "path", "url"... properties can be used

        :param instance: FileField
        """
        field = getattr(instance, self.name)
        if field:
            for variation in self.variations:
                variation_name = self.attr_class.get_variation_name(field, variation)
                variation_field = ImageFieldFile(instance, self, variation_name)
                setattr(field, variation['name'], variation_field)


    def contribute_to_class(self, cls, name):
        """Call methods for generating all operations on specified signals"""

        super(GingerImageField, self).contribute_to_class(cls, name)
        signals.post_init.connect(self.set_variations, sender=cls)
        signals.post_delete.connect(self.delete_variations, sender=cls)

    def delete_variations(self, instance=None, **kwargs):
        field = getattr(instance, self.name)
        if field:
            field.delete(False)

