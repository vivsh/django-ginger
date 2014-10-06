
from django.core.exceptions import ImproperlyConfigured
from django.core.signing import get_cookie_signer

from django import  test
from django.dispatch import receiver
from django.test.utils import override_settings
from .forms import StagingForm
from .middleware import StagingMiddleware
from . import views, conf


@receiver(test.signals.setting_changed)
def refresh_conf(**kwargs):
    from ginger.staging.conf import reload_settings
    reload_settings()


class TestForms(test.SimpleTestCase):

    @override_settings(STAGING_SECRET="secret")
    def test_invalid(self):
        data = {"secret": "anything"}
        form = StagingForm(data)
        self.assertFalse(form.is_valid())

    @override_settings(STAGING_SECRET="password")
    def test_valid(self):
        data = {"secret": "password"}
        form = StagingForm(data)
        self.assertTrue(form.is_valid())


@override_settings(STAGING_SECRET="secret")
class TestMiddleware(test.SimpleTestCase):

    def sign_cookie(self, request, value):
        from ginger.staging.conf import STAGING_SESSION_KEY
        cookies = request.COOKIES
        signer = get_cookie_signer(STAGING_SESSION_KEY)
        sign = signer.sign(value)
        cookies[STAGING_SESSION_KEY] = sign

    def cookie_request(self, value, **headers):
        conf.reload_settings()
        fac = test.RequestFactory()
        request = fac.get("/")
        cookies = {}
        request.COOKIES = cookies
        self.sign_cookie(request, value, **headers)
        return request

    @override_settings(STAGING_SECRET=None)
    def test_missing_secret(self):
        self.assertRaises(ImproperlyConfigured, StagingMiddleware)

    @override_settings(STAGING_SECRET="password")
    def test_valid_secret(self):
        ware = StagingMiddleware()
        self.assertIsNotNone(ware)

    @override_settings(STAGING_SECRET="password")
    def test_valid_cookie(self):
        request = self.cookie_request("password")
        middleware = StagingMiddleware()
        response = middleware.process_request(request)
        self.assertIsNone(response)

    def test_invalid_cookie(self):
        request = self.cookie_request("anything")
        middleware = StagingMiddleware()
        response = middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 401)



@override_settings(STAGING_SECRET="secret")
class TestViews(test.SimpleTestCase):

    def test_get(self):
        fac = test.RequestFactory()
        request = fac.get("/")
        response = views.stage(request)
        self.assertEqual(response.status_code, 401)
        form = response.context_data['form']
        self.assertIsInstance(form, StagingForm)
        self.assertFalse(form.is_bound)


    @override_settings(STAGING_SECRET="password", STAGING_ALLOWED_HOSTS=["curry.com"])
    def test_post_valid_host(self):
        from ginger.staging.conf import STAGING_SESSION_KEY
        fac = test.RequestFactory()
        request = fac.post("/", data={'secret': 'password'}, HTTP_HOST="curry.com")
        request.COOKIES = {}
        response = views.stage(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(STAGING_SESSION_KEY, response.cookies)

    @override_settings(STAGING_SECRET="password", STAGING_ALLOWED_HOSTS=["curry.com"])
    def test_post_invalid_host(self):
        from ginger.staging.conf import STAGING_SESSION_KEY
        fac = test.RequestFactory()
        request = fac.post("/", data={'secret': 'password'}, HTTP_HOST="potato.com")
        request.COOKIES = {}
        response = views.stage(request)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(STAGING_SESSION_KEY, response.cookies)
