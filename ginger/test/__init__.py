from django import test
import json
from django.contrib.auth.models import AnonymousUser


class TestRequestMixin(object):

    def request(self, method="GET", path="/", session=None, user=None, data=None, **kwargs):
        factory = test.RequestFactory()
        if data is not None and kwargs.get("content_type", "application/json"):
            data = json.dumps(data)
        kwargs['data'] = data
        request = getattr(factory, method.lower())(path, **kwargs)
        request.session = {} if session is None else session
        request.user = user or AnonymousUser()
        return request


class TestView(test.SimpleTestCase):
    view_class = None


class TestForm(test.SimpleTestCase):

    def get_form_kwargs(self, kwargs):
        return kwargs or {}

    def get_form_class(self):
        return self.form_class

    def get_form(self, form_kwargs=None):
        if form_kwargs is None:
            form_kwargs = {}
        return self.get_form_class()(self.get_form_kwargs(form_kwargs))

    def get_bound_field(self, field_name, form_kwargs=None):
        return self.get_form(form_kwargs)[field_name]

    def get_field(self, field_name, form_kwargs=None):
        return self.get_form(form_kwargs).fields[field_name]

    def assertFormValid(self, form_kwargs, msg=None):
        form = self.get_form(form_kwargs)
        if msg is None:
            msg = "Form is not valid. ErrorDict: %s" % form.errors
        self.assertTrue(form.is_valid(), msg)

    def assertFieldExists(self, field_name, form_kwargs=None, msg=None):
        form = self.get_form(form_kwargs)
        if msg is None:
            msg = "Nof field %r found in %r" % (field_name, self.get_form_class())
        self.assertIn(field_name, form.fields, msg)

    def assertFormResultEquals(self, form_kwargs, result, msg=None):
        form = self.get_form(form_kwargs)
        self.assertTrue(form.result, result, msg)

    def assertFormInvalid(self, form_kwargs, msg=None):
        form = self.get_form(form_kwargs)
        if msg is None:
            msg = "Form is not invalid"
        self.assertFalse(form.is_valid(), msg)

    def assertFieldInvalid(self, field_name, form_kwargs):
        form = self.get_form(form_kwargs)
        errors = form[field_name].errors
        self.assertTrue(errors)

    def assertFieldValid(self, field_name, form_kwargs):
        field = self.get_bound_field(field_name, form_kwargs)
        errors = field.errors
        self.assertFalse(errors)

    def assertFormErrorContains(self, field_name, form_kwargs, msg=None):
        form = self.get_form(form_kwargs)
        if msg is None:
            msg = "Form is not invalid"
        self.assertIn(field_name, form.errors, msg)
