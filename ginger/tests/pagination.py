
import mock
import random
from django import test
from django.utils import six
from ginger import utils
from ginger.paginator import GingerPaginator


def parse_url(url):
    parts = six.moves.urllib.parse.urlparse(url)
    return six.moves.urllib.parse.parse_qs(parts.query)


class TestGingerPaginator(test.SimpleTestCase):

    def setUp(self):
        self.factory = test.RequestFactory()

    def request(self, **kwargs):
        return self.factory.get("/", data=kwargs)

    def test_missing_page(self):
        pass

    def test_invalid_page(self):
        pass

    def test_valid_page(self):
        request = self.request()
        # paginator = GingerPaginator([], per_page=10, page_limit=limit, parameter_name=param)

    def test_constructor(self):
        param = "pg"
        limit = random.randint(10, 100)
        paginator = GingerPaginator([], per_page=10, page_limit=limit, parameter_name=param)
        self.assertEqual(paginator.page_limit, limit)
        self.assertEqual(paginator.parameter_name, param)

    def test_page(self):
        param = "pg"
        paginator = GingerPaginator([i for i in range(100)], per_page=10, parameter_name=param)
        page_num = random.randint(1, 9)
        req = self.request(**{param: page_num})
        page = paginator.page(req)
        self.assertEqual(page.request, req)
        self.assertEqual(page.parameter_name, param)
        self.assertEqual(page.number, page.number)
        page_links = page.build_links()
        self.assertTrue(page_links)


class TestPageLink(test.SimpleTestCase):

    def setUp(self):
        self.factory = test.RequestFactory()

    def request(self, **kwargs):
        return self.factory.get("/random/path/", data=kwargs)

    def page_link(self, index, value, name="page"):
        request = self.request(**{name: value})
        page = mock.Mock()
        page.number = value
        page.request = request
        page.parameter_name = name
        return PageLink(page, index)

    def test_url(self):
        page_link = self.page_link(1, 5)
        url = page_link.url
        params = parse_url(url)
        self.assertEqual(params["page"], ["1"])

    def test_active(self):
        page_link = self.page_link(5, 5)
        self.assertTrue(page_link.is_active)

    def test_inactive(self):
        page_link = self.page_link(5, 5)
        self.assertTrue(page_link.is_active)

    def test_index(self):
        page_link = self.page_link(5, 5)
        self.assertEqual(page_link.index, 5)



