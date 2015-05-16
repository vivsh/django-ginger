
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from django.utils.decorators import method_decorator

from django.utils.functional import cached_property
from django.views.generic import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ginger import serializer
from ginger.exceptions import (
    MethodNotFound, BadRequest
)

from .base import GingerView

__all__ = ['GingerJSONView']


logger = logging.getLogger('ginger.views')


class GingerJSONView(GingerView):

    MAX_CONTENT_SIZE = 32 * 1024

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        try:
            self.process_request(request)
            method = request.method.lower()
            func = getattr(self, method, None)
            if not func:
                raise MethodNotFound
            params = self.get_params()
            if isinstance(params, dict):
                payload = func(**params)
            elif params:
                raise BadRequest("Invalid parameters format")
            if hasattr(payload, 'to_json'):
                payload = payload.to_json()
            status = 200
        except Exception as exc:
            status, payload = serializer.process_exception(request, exc)
            if status == 500:
                logger.exception("Operation failed")
        return self.render_to_response(payload, status=status)

    def get_serializers(self):
        return getattr(self, 'serializers', {})

    def render_to_response(self, payload, **kwargs):
        content = serializer.encode(payload, serializers=self.get_serializers())
        kwargs.setdefault('status', 200)
        kwargs.setdefault('content_type', 'application/json')
        return HttpResponse(content, **kwargs)

    def get_params(self):
        return self.JSON

    @cached_property
    def JSON(self):
        request = self.request
        limit = self.MAX_CONTENT_SIZE
        content = request.read(limit)
        if not content:
            payload = {}
        else:
            try:
                payload = serializer.decode(content)
            except ValueError:
                raise BadRequest("Invalid json format: %r" % content)
        return payload
