
from django.utils import six
import abc
import copy
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import File


class StorageFile(object):

    data = None

    def delete(self, file_storage):
        field_dict = self.data
        if isinstance(field_dict, File):
            file_name = field_dict.name
        else:
            field_dict = field_dict.copy()
            file_name = field_dict.pop('tmp_name')
        file_storage.delete(file_name)

    def load(self, file_storage):
        field_dict = self.data
        field_dict = field_dict.copy()
        tmp_name = field_dict.pop('tmp_name')
        return UploadedFile(file=file_storage.open(tmp_name), **field_dict)

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
#         field_file.close()

    def is_stored(self):
        return isinstance(self.data, dict)


def store_files(file_storage, data):
    for k,v in data.items():
        if isinstance(v, File):
            pfile = StorageFile()
            pfile.store(file_storage, v)
            data[k]= pfile
    return data

def load_files(file_storage, form_data):
    data = copy.copy(form_data)
    for k,v in form_data.iteritems():
        if isinstance(v, StorageFile):
            data[k]= v.load(file_storage)
    return data

def delete_files(file_storage, data):
    for _,v in data.items():
        if isinstance(v, File):
            file_name = v.name
            file_storage.delete(file_name)
        elif isinstance(v, StorageFile):
            v.delete(file_storage)
    return data


@six.add_metaclass(abc.ABCMeta)
class Storage(object):

    @abc.abstractmethod
    def get_form_data(self, step_name):
        """

        :param step_name:
        :return:
        """

    @abc.abstractmethod
    def set_form_data(self, step_name, data, files):
        """

        :param step_name:
        :param data:
        :param files:
        :return:
        """

    @abc.abstractmethod
    def clear_form_data(self):
        """

        :return:
        """

    @abc.abstractmethod
    def get_data_for_done(self):
        """

        :return:
        """

    @abc.abstractmethod
    def set_data_for_done(self, data):
        """

        :param data:
        :return:
        """



class SessionStorage(Storage):

    data = None

    def __init__(self, wizard, prefix=""):
        self.wizard = wizard
        self.request = wizard.request
        self.prefix = prefix
        self.done_key = self.create_key("done")
        self.step_key = self.create_key("step")
        self._load_data()

    def _load_data(self):
        session = self.request.session
        self.data = session.get(self.step_key)
        if not isinstance(self.data, dict):
            self.data = {}

    def _save_data(self):
        self.request.session[self.step_key] = self.data
        self.request.session.modified = True

    def create_key(self, suffix):
        oid = self.wizard.class_oid()
        return "%s%s-%s" % (self.prefix, oid, suffix)

    def get_data_for_done(self):
        return self.request.session.get(self.done_key)

    def set_data_for_done(self, data):
        self.request.session[self.done_key] = data

    def set_form_data(self, step_name, data, files):
        self.data[step_name] = data, files
        self._save_data()

    def get_form_data(self, step_name):
        if step_name in self.data:
            return self.data[step_name]
        return None, None

    def clear_form_data(self):
        self.data.clear()
        self._save_data()

