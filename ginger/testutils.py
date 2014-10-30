
import json
from django import test
from django.contrib.auth.models import AnonymousUser


__all__ = ['TestRequestMixin']


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

