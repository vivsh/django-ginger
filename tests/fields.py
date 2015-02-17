
from django import test, forms
from ginger.forms import FileOrUrlInput


class DummyForm(forms.Form):
    file = forms.FileField(widget=FileOrUrlInput, required=False)

class RequiredDummyForm(forms.Form):
    file = forms.FileField(widget=FileOrUrlInput, required=True)


class TestFileOrUrlInput(test.SimpleTestCase):
    image_url = "http://media-cache-ec0.pinimg.com/236x/cb/99/03/cb9903c463fda9a46f6d79005f29a9be.jpg"

    def test_valid(self):
        form = DummyForm(data={"file": self.image_url}, files={})
        self.assertTrue(form.is_valid())
        file_obj = form.cleaned_data["file"]
        self.assertEqual(file_obj.url, self.image_url)

    def test_contradiction(self):
        form = DummyForm(data={"file": self.image_url,
                               "file-clear": "on"}, files={})
        self.assertFalse(form.is_valid())