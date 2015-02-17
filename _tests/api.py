
import mock
from django.contrib.auth.models import AnonymousUser
from ginger.forms import GingerForm
import json
from datetime import date, time, datetime
from django import test, forms
from django.core.paginator import Paginator

from ginger import serializer, exceptions, views, forms as jforms
from django.test.utils import override_settings
from django.core.exceptions import PermissionDenied
from ginger.exceptions import PermissionRequired, ValidationFailure


class DummyClass(object):
    name = "hello"


class TestSerializers(test.SimpleTestCase):

    def test_datetime(self):
        now = datetime.now()
        value = serializer.encode({'now': now})
        self.assertTrue(value)

    def test_date(self):
        now = date.today()
        value = serializer.encode({'now': now})
        self.assertTrue(value)

    def test_time(self):
        now = time()
        value = serializer.encode({'now': now})
        self.assertTrue(value)

    def test_dummy_class(self):
        obj = DummyClass()
        self.assertRaises(TypeError, lambda : serializer.encode(obj))
        value = serializer.encode(obj, serializers={DummyClass: lambda o: o.name})
        self.assertEqual(value, '"hello"', value)

    def test_page(self):
        total = 200
        object_list = list(range(total))
        num = 3
        pg = Paginator(object_list, per_page=10).page(num)
        result = json.loads(serializer.encode(pg))
        self.assertEqual(result['total'], total)
        self.assertEqual(result['per_page'], 10)
        self.assertEqual(result['start_index'], 21)
        self.assertEqual(result['end_index'], 30)
        self.assertEqual(result['index'], num)


class ValidationForm(GingerForm):
    name = forms.CharField(max_length=100)
    age = forms.IntegerField(min_value=0)


class TestExceptions(test.SimpleTestCase):

    def test_error(self):
        msg = "Some random message"
        status = 200
        error = exceptions.GingerHttpError(msg)
        error.status_code = status
        data = error.to_json()
        self.assertEqual(error.description, msg)
        self.assertEqual(data['message'], msg)
        self.assertEqual(data['type'], 'GingerHttpError')

    def test_notfound(self):
        errcls = exceptions.NotFound
        self.assertEqual(errcls.status_code, 404)
        self.assertEqual(errcls().to_json()['type'], 'NotFound')

    def test_methodnotfound(self):
        errcls = exceptions.MethodNotFound
        self.assertEqual(errcls.status_code, 405)
        self.assertEqual(errcls().to_json()['type'], 'MethodNotFound')

    def test_permissionrequired(self):
        errcls = exceptions.PermissionRequired
        self.assertEqual(errcls.status_code, 401)
        self.assertEqual(errcls().to_json()['type'], 'PermissionRequired')

    def test_loginrequired(self):
        errcls = exceptions.LoginRequired
        self.assertEqual(errcls.status_code, 401)
        self.assertEqual(errcls().to_json()['type'], 'LoginRequired')

    def test_validationfailure(self):
        self.assertEqual(exceptions.ValidationFailure.status_code, 422)
        name = "asd"*300
        age = -1
        msg = "Failed"
        form = ValidationForm(data={'name': name, 'age': age})
        form.failure_message = msg
        self.assertFalse(form.is_valid())
        data = exceptions.ValidationFailure(form).to_json()
        self.assertEqual(data['message'], msg, data)
        self.assertIn('name', data['data'])
        self.assertIn('age', data['data'])


class TestJSONView(test.SimpleTestCase):

    def create_view(self, **kwargs):
        cls = type("anything", (views.GingerJSONView,) , kwargs)
        return cls.as_view()

    def create_request(self, method, payload):
        factory = test.RequestFactory()
        kwargs = {}
        if payload is not None:
            content = json.dumps(payload)
            kwargs['content_type'] = 'application/json'
            kwargs['data'] = content
        request = getattr(factory, method)("/", **kwargs)
        request.user = AnonymousUser()
        return request

    def get_response(self, method, payload, **view_kwargs):
        view = self.create_view(**view_kwargs)
        req = self.create_request(method, payload)
        response = view(req)
        response.json = json.loads(response.content)
        return response

    def test_max_content_size(self):
        """
        Size of request cannot be larger than the specified MAX_CONTENT_SIZE attribute
        """
        payload = {'value': '****'*(20*1024)}
        resp = self.get_response('post', payload, post=lambda _, **kwargs: {'kwargs': kwargs})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json['type'], 'BadRequest')

    def test_bad_request(self):
        """
        Content of the body should be valid json
        """
        factory = test.RequestFactory()
        req = factory.post("/", content_type="application/json", data="asdasdasdasdasdasdasd")
        req.user = None
        view = self.create_view(post=lambda _, **kwargs: {'kwargs': kwargs})
        resp = view(req)
        result = json.loads(resp.content)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(result['type'], 'BadRequest')

    def test_missing_method(self):
        payload = {}
        resp = self.get_response('post', payload)
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(resp.json['type'], 'MethodNotFound')

    def test_result(self):
        payload = {'name': 'Zail Singh'}
        resp = self.get_response('post', payload, post=lambda _, **kwargs: {'kwargs': kwargs})
        self.assertEqual(resp.json, {'kwargs': payload})

    def test_empty_request_body(self):
        payload = {'name': 'Zail Singh'}
        resp = self.get_response('post', {}, post=lambda _: payload)
        self.assertEqual(resp.json, payload)

    def test_get_request(self):
        payload = {'name': 'Zail Singh'}
        factory = test.RequestFactory()
        req = factory.get("/", data={}, content_type='application/json')
        req.user = AnonymousUser()
        view = self.create_view(get=lambda _: payload)
        resp = view(req)
        resp.json = json.loads(resp.content)
        self.assertEqual(resp.json, payload)

    def test_internal_error(self):
        payload = {'name': 'Zail Singh'}
        def func(_, **kwargs):
            raise ValueError("Something didn't go right !")
        resp = self.get_response('post', payload, post=func)
        self.assertEqual(resp.status_code, 500)
        self.assertIn('message', resp.json)

    @override_settings(DEBUG=True)
    def test_error_with_debug(self):
        payload = {'name': 'Zail Singh'}
        msg = "Something didn't go right !"
        def func(_, **kwargs):
            raise ValueError(msg)
        resp = self.get_response('post', payload, post=func)
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.json['type'], 'ValueError')
        self.assertEqual(resp.json['message'], msg)
        self.assertIsNotNone(resp.json['traceback'])

    def test_permission_denied(self):
        payload = {'name': 'Zail Singh'}
        def func(_, **kwargs):
            raise PermissionDenied
        resp = self.get_response('post', payload, post=func)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json['type'], 'PermissionDenied')

    def test_json_error(self):
        payload = {'name': 'Zail Singh'}
        def func(_, **kwargs):
            raise PermissionRequired
        resp = self.get_response('post', payload, post=func)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json['type'], 'PermissionRequired')


class DummyContextMixin(jforms.GingerFormMixin):

    called = False

    def process_context(self, context):
        self.called = True
        return context


class TestGingerForm(test.SimpleTestCase):

    def test_constructor(self):
        values = dict(name="Zail", age=81)
        form_obj = DummyContextMixin(**values)
        self.assertTrue(form_obj.called)
        context = form_obj.context
        self.assertEqual(context, values)

    def test_constructor_instance(self):
        values = dict(instance=100)
        form_obj = jforms.GingerFormMixin(**values)
        context = form_obj.context
        self.assertTrue(context)
        self.assertEqual(context['instance'], 100)

    def test_run_without_context(self):
        class MockForm(jforms.GingerForm):
            age = forms.IntegerField(max_value=38, min_value=18)

            def execute(self, name):
                age = self.cleaned_data['age']
                return {'age': age, 'name': name}

        form = MockForm(data={'age': 20})
        self.assertRaises(TypeError, form.run)


    def test_valid_run(self):
        template = "%(name)s has age = %(age)d"

        class MockForm(jforms.GingerForm):
            age = forms.IntegerField(max_value=38, min_value=18)

            def execute(self, name):
                age = self.cleaned_data['age']
                return template%{'age': age, 'name': name}

        form = MockForm(data={'age': 20}, name='Zail')
        result = form.run()
        self.assertEqual(result, template%dict(age=20, name="Zail"))

    def test_invalid_run(self):
        template = "%(name)s has age = %(age)d"

        class MockForm(jforms.GingerForm):
            age = forms.IntegerField(max_value=38, min_value=18)

            def execute(self, name):
                age = self.cleaned_data['age']
                return template%{'age': age, 'name': name}

        form = MockForm(data={'age': 200}, name='Zail')
        self.assertRaises(ValidationFailure, form.run)
        self.assertIn('age',form.errors)

    def test_add_error(self):
        msg = "I didn't like this name"
        name = "Zail"

        class MockForm(jforms.GingerForm):
            name = forms.CharField(max_length=20)

        form = MockForm(data={'name': name})
        form.is_valid()
        self.assertEqual(name, form.cleaned_data['name'])
        self.assertFalse(form.errors)
        form.add_error("name", msg)
        errors = ValidationFailure(form).to_json()
        self.assertEqual(msg, errors['data']['name'][0]['message'], errors)
        self.assertNotIn('name', form.cleaned_data)

    def test_invalid_with_add_error(self):
        template = "%(name)s has age = %(age)d"

        class MockForm(jforms.GingerForm):
            age = forms.IntegerField(max_value=38, min_value=18)

            def execute(self, name):
                age = self.cleaned_data['age']
                self.add_error('age', "I don't like 20years")
                return template%{'age': age, 'name': name}

        form = MockForm(data={'age': 20}, name='Zail')
        self.assertRaises(ValidationFailure, form.run)
        self.assertIn('age',form.errors)


class TestSearchForm(test.TestCase):
    pass
