from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from os.path import join as joinpath, dirname
from django import test
from ginger.views.storages import  StorageFile

MEDIA_ROOT = joinpath(dirname(__file__), "media")


@test.override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TestStorageFile(test.SimpleTestCase):

    def setUp(self):
        self.filename = joinpath(MEDIA_ROOT, "random.txt")
        self.file_storage = FileSystemStorage(MEDIA_ROOT)
        self.file = StorageFile()

    def test_some(self):
        self.file.store(self.file_storage, File(open(self.filename)))
        print(self.file.data)


