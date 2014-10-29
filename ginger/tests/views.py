
from os.path import join as joinpath, dirname, realpath
import json
import mock

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django import test
from django.http.response import Http404
from django.test.utils import override_settings

from django import forms
from ginger.forms import GingerForm
from ginger.templates import GingerResponse
from ginger import templates, views


_root = dirname(realpath(__file__))
TEMPLATE_DIR = joinpath(_root, "templates")
MEDIA_ROOT = joinpath(_root, "media")


class TestGingerResponse(test.SimpleTestCase):

    def setUp(self):
        self.factory = test.RequestFactory()
        self.request = self.factory.get("/random/path/")

    def test_html(self):
        value = "mickey mouse"
        template = templates.from_string("{{name}}")
        resp = GingerResponse(self.request, template, {"name": value})
        content = resp.render().content
        self.assertEqual(content, value)

    def test_json(self):
        value = "mickey mouse"
        template = templates.from_string("{{name}}")
        resp = GingerResponse(self.request, template, {"name": value},
                              content_type="application/json")
        content = resp.render().content
        self.assertEqual(content, json.dumps({"name": value}))


class RandomView(views.GingerTemplateView):
    url = None
    template_name = "anything.html"

    def get(self, request, *args):
        return self.redirect(self.url)


class TestGingerView(test.SimpleTestCase):

    def setUp(self):
        self.factory = test.RequestFactory()
        self.request = self.factory.get("/random/path/")
        self.request.user = "fake"
        self.view_class = RandomView

    def test_method_not_found(self):
        response = views.GingerView.as_view()(self.request)
        self.assertEqual(response.status_code, 405)


class TestGingerTemplateView(test.SimpleTestCase):

    def setUp(self):
        self.factory = test.RequestFactory()
        self.request = self.factory.get("/random/path/")
        self.request.user = "fake"
        self.view_class = RandomView

    def test_ajax_redirect(self):
        url = "/home/"
        view = self.view_class.as_view(url=url)
        request = self.factory.get("/anything/", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = "fake"
        response = view(request)
        context = response.context_data
        self.assertEqual(context['data']['url'], url)

    def test_non_ajax_redirect(self):
        url = "/home/"
        view = self.view_class.as_view(url=url)
        request = self.factory.get("/anything/")
        request.user = "fake"
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,url)

    def test_render(self):
        class AnotherView(views.GingerTemplateView):
            template_name = "anything.html"
        request = self.request
        response = AnotherView.as_view()(request)
        self.assertEqual(response.template_name, ["anything.html"])


class FakeInfo(GingerForm):

    name = forms.CharField(max_length=100)
    age = forms.IntegerField(max_value=100, min_value=10)

    def execute(self, **kwargs):
        return {"name": self.cleaned_data["name"]}


class FakeLocation(GingerForm):
    address = forms.CharField(max_length=100)


class FakeFormDone(views.GingerFormDoneView):

    form_class = FakeInfo
    template_name = "wizard.html"

    def get_step_url(self, step_name):
        return "/form/%s/" % step_name if step_name else "/form/"


class FakeWizard(views.GingerWizardView):
    first = views.Step(label="First", when="check", form=FakeInfo)
    second = views.Step(label="Second", form=FakeLocation)

    checked = True

    template_format = "wizard%(step)s.html"

    def check(self):
        return self.checked

class TestSteps(test.SimpleTestCase):

    def setUp(self):
        self.view = FakeWizard.as_view()
        self.factory = test.RequestFactory()

    def test_step_list(self):
        wiz = FakeWizard()
        self.assertEqual(len(wiz.steps), 2)
        self.assertEqual(wiz.steps.names(), ['first', 'second'])
        self.assertEqual(wiz.steps.first.name, "first")
        self.assertEqual(wiz.steps.last.name, "second")
        self.assertEqual(wiz.steps['second'].name, "second")
        self.assertEqual(wiz.steps['second'].previous(), wiz.steps['first'])
        self.assertEqual(wiz.steps['first'].next(), wiz.steps['second'])
        self.assertEqual(wiz.steps.first, wiz.steps['first'])
        self.assertEqual(wiz.steps.last, wiz.steps['second'])
        self.assertTrue(wiz.steps['second'].is_last())
        self.assertFalse(wiz.steps['first'].is_last())
        self.assertTrue(wiz.steps['first'].is_first())
        self.assertFalse(wiz.steps['second'].is_first())

    def test_step_enabled(self):
        wiz = FakeWizard()
        self.assertEqual(len(wiz.steps), 2)
        wiz.checked = False
        self.assertEqual(len(wiz.steps), 1)
        self.assertRaises(ValueError, lambda : wiz.steps['first'])
        self.assertEqual(wiz.steps.first, wiz.steps['second'])



@override_settings(TEMPLATE_DIRS=(TEMPLATE_DIR,))
class TestGingerFormDone(test.SimpleTestCase):

    def setUp(self):
        self.view = FakeFormDone.as_view()
        self.factory = test.RequestFactory()

    def request(self, path, method="GET", user=AnonymousUser(), session=None, **kwargs):
        request = getattr(self.factory, method.lower())(path, **kwargs)
        request.session = session if session is not None else {}
        request.user = user
        return request

    def test_redirect_on_invalid_done(self):
        request = self.request("/form/done/")
        response = self.view(request, step=FakeFormDone.done_step)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/form/", "Expected %r but got %r" % ("/form/", response.url))

    def test_valid_get(self):
        request = self.request("/form/")
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_invalid_get(self):
        request = self.request("/form/sadasda/")
        self.assertRaises(Http404, self.view, request, step="asdasdas")

    def test_template(self):
        wiz = FakeFormDone()
        wiz.is_done_step = lambda: False
        template_names = wiz.get_template_names()
        self.assertEqual(template_names, ["wizard.html"])

    def test_template_for_done(self):
        wiz = FakeFormDone()
        wiz.is_done_step = lambda: True
        template_names = wiz.get_template_names()
        self.assertEqual(template_names, ["wizard_done.html"])

    def test_valid_post(self):
        session = {}
        name = "asdasda asdasd"
        request = self.request("/form/", method="post",
                               data={"name": name, "age": 32}, session=session)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/form/done/")

    def test_invalid_post(self):
        session = {}
        name = "asdasda asdasd"
        request = self.request("/form/", method="post",
                               data={"name": name, "age": 320}, session=session)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context_data['form'].errors)


    def test_done(self):
        session = {}
        name = "asdasda asdasd"
        request = self.request("/form/", method="post",
                               data={"name": name, "age": 32}, session=session)
        temp = self.view(request)
        request = self.request("/form/done/", session=session)
        response = self.view(request, step=FakeFormDone.done_step)
        self.assertEqual(response.status_code, 200)

        key = response.context_data["view"].get_session_key()

        self.assertEqual(response.context_data["name"], name, response.context_data)
        self.assertEqual(session[key]["name"], name)


class FakeWizard2(FakeWizard):

    def get_step_url(self, step_name):
        return "/wizard/%s/"%step_name


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT,
    TEMPLATE_DIRS=(joinpath(dirname(realpath(__file__)), "templates"),))
class TestWizard(test.SimpleTestCase):

    def setUp(self):
        self.view = FakeWizard.as_view()
        self.view2 = FakeWizard2.as_view()
        self.factory = test.RequestFactory()

    def request(self, path="/wizard/anything/", method="GET", user=AnonymousUser(), session=None, url_name="anything", **kwargs):
        request = getattr(self.factory, method.lower())(path, **kwargs)
        request.session = session if session is not None else {}
        request.user = user
        request.resolver_match = mock.MagicMock
        request.resolver_match.url_name = url_name
        return request

    def test_valid_step(self):
        request = self.request("/wizard/first/")
        response = self.view(request, step="first")
        self.assertEqual(response.status_code, 200)

        response = self.view(request, step="second")
        self.assertEqual(response.status_code, 200)

    def test_invalid_step(self):
        request = self.request()
        self.assertRaises(Http404, self.view, request, step="asdasdasd")

    @mock.patch("ginger.views.generic.reverse")
    def test_step_url(self, mock_reverse):
        request = self.request()
        mock_reverse.return_value = "/some_url/"
        wiz = FakeWizard()
        wiz.request = request
        wiz.args = ()
        wiz.kwargs = {}
        url = wiz.get_step_url("first")
        self.assertTrue(mock_reverse.called)
        self.assertTrue(mock_reverse.called_once_with("anything", args=(), kwargs={"step": "first"}))
        self.assertEqual(url, "/some_url/")

    def test_empty_step(self):
        request = self.request()
        response = self.view2(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/wizard/first/")
    #
    def test_invalid_form_class(self):
        self.assertRaises(ImproperlyConfigured, lambda: views.Step(form=None))

    def test_invalid_done(self):
        request = self.request()
        response = self.view2(request, step=FakeWizard2.done_step)
        self.assertEqual(response.status_code, 302)

    def test_delete_old_files(self):
        FakeWizard2.delete_old_files(seconds=10)

