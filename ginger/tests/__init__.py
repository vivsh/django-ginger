
from django import test


class TestFake(test.TestCase):

    def test_anything(self):
        self.assertEqual(1,2, "This should've been equal")