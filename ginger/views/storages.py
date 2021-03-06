
import copy
from django.utils import six
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import File


__all__ = ['FormStorageBase', 'SessionFormStorage']


class StorageFile(object):

    data = None

    def load(self, file_storage):
        field_dict = self.data
        field_dict = field_dict.copy()
        tmp_name = field_dict.pop('tmp_name')
        file_obj = UploadedFile(file=file_storage.open(tmp_name), **field_dict)
        file_obj.url = file_storage.url(tmp_name)
        return file_obj

    def store(self, file_storage, field_file):
        tmp_filename = file_storage.save(field_file.name, field_file)
        file_dict = {
            'tmp_name': tmp_filename,
            'name': field_file.name,
            'content_type': getattr(field_file,'content_type',None),
            'size': field_file.size,
            'charset': getattr(field_file,'charset',None)
        }
        self.data = file_dict

    def has_file(self):
        return isinstance(self.data, dict)


class FormStorageBase(object):

    data = None

    def __init__(self, wizard, autocommit=True, prefix=""):
        self.wizard = wizard
        self.file_storage = wizard.file_storage
        self.autocommit = autocommit
        self.prefix = prefix
        self.step_key = self.create_key("steps")
        self._load_data()

    def reduce_files(self, data):
        for k, v in six.iteritems(data.copy()):
            if isinstance(v, File):
                file = StorageFile()
                file.store(self.file_storage, v)
                data[k] = file
        return data

    def restore_files(self, form_data):
        data = copy.copy(form_data)
        for k, v in form_data.iteritems():
            if isinstance(v, StorageFile):
                data[k] = v.load(self.file_storage)
        return data

    def create_key(self, suffix):
        oid = self.wizard.class_oid()
        return "%s%s-%s" % (self.prefix, oid, suffix)

    def set(self, step_name, data, files):
        self.data[step_name] = data, self.reduce_files(files)
        if self.autocommit:
            self._save_data()

    def get(self, step_name):
        try:
            data, files = self.data[step_name]
        except KeyError:
            return None, None
        else:
            return data, self.restore_files(files)

    def clear(self):
        self.data.clear()
        if self.autocommit:
            self._save_data()

    def _load_data(self):
        self.data = self.load()
        if not isinstance(self.data, dict):
            self.data = {}

    def _save_data(self):
        self.store(self.data)

    def store(self, data):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError



class SessionFormStorage(FormStorageBase):

    @property
    def session(self):
        return self.wizard.request.session

    def load(self):
        return self.session.get(self.step_key)

    def store(self, data):
        self.session[self.step_key] = data
        self.session.modified = True
