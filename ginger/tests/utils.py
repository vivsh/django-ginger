
from django import test
from django.utils import six

from ginger import utils



class TestGeneratePages(test.SimpleTestCase):

    def pages(self, index, limit, total):
        return list(utils.generate_pages(index, limit, total))

    def test_index_le_one(self):
        self.assertEqual(1, self.pages(0, 10, 100)[0])
        self.assertEqual(1, self.pages(-10, 10, 100)[0])

    def test_limit_gt_total(self):
        """
        When limit is more than total, then total == len(result)
        """
        result = self.pages(1, 100, 10)
        self.assertEqual(len(result), 10, result)

    def test_total_gt_limit(self):
        result = self.pages(1, 10, 100)
        self.assertEqual(len(result), 10, result)

    def test_index_gt_total(self):
        result = self.pages(110, 10, 100)
        self.assertEqual(len(result), 10, result)
        self.assertEqual(result, range(91, 101), result)

    def test_cases(self):
        self.assertEqual(self.pages(7, 10, 10)[0], 1)
        self.assertEqual(len(self.pages(7, 1, 10)), 1)
        self.assertEqual(self.pages(7, 1, 10)[0], 7)
        self.assertEqual(self.pages(7, 2, 10), [7, 8])
        self.assertEqual(self.pages(8, 3, 8), [6, 7, 8])


class TestUrlModifier(test.SimpleTestCase):

    def setUp(self):
        self.factory = test.RequestFactory()

    def request(self, data, values, append):
        request = self.factory.get("/", data=data)
        url = utils.get_url_with_modified_params(request, values, append=append)
        parts = six.moves.urllib.parse.urlparse(url)
        return six.moves.urllib.parse.parse_qs(parts.query)

    def test_param_replace(self):
        old = {"param": 90}
        values = {"param": 10}
        result = self.request(old, values, append=False)
        self.assertEqual(result["param"], ["10"])

    def test_param_removal(self):
        old = {"param": 90}
        values = {"param": ""}
        result = self.request(old, values, append=False)
        self.assertNotIn("param", result)

    def test_param_append(self):
        old = {"param": 90}
        values = {"param": 10}
        result = self.request(old, values, append=True)
        self.assertEqual(result["param"], ["90", "10"])


def random_function():
    pass


class TestQualifiedName(test.SimpleTestCase):

    def test_method(self):
        name = utils.qualified_name(self.test_method)
        self.assertIsNotNone(name)

    def test_unbound_method(self):
        name = utils.qualified_name(self.test_method)
        self.assertIsNotNone(name)

    def test_function(self):
        name = utils.qualified_name(random_function)
        self.assertIsNotNone(name)

    def test_class(self):
        name = utils.qualified_name(TestQualifiedName)
        self.assertIsNotNone(name)