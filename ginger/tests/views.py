
from django import test
import json
from ginger.templates import GingerResponse
from ginger import templates


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