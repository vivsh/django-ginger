
import logging
import traceback

from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from ginger import serializers
from ginger.exceptions import (
    MethodNotFound, BadRequest, GingerHttpError, NotFound,
    PermissionDenied, Http404
)
from serializers import process_exception


logger = logging.getLogger('ginger.views')


class JSONView(View):

    MAX_CONTENT_SIZE = 32 * 1024

    def check_access(self, request):
        return

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        try:
            self.check_access(request)
            method = request.method.lower()
            func = getattr(self, method, None)
            if not func:
                raise MethodNotFound
            params = self.get_params()
            if isinstance(params, dict):
                payload = func(**params)
            elif params:
                raise BadRequest
            if hasattr(payload, 'to_json'):
                payload = payload.to_json()
            status = 200
        except Exception as exc:
            status, payload = process_exception(exc)
            if status == 500:
                logger.exception("Operation failed")
        return self.render_to_response(payload, status=status)

    def get_serializers(self):
        return getattr(self, 'serializers', {})

    def render_to_response(self, payload, **kwargs):
        content = serializers.encode(payload, serializers=self.get_serializers())
        kwargs.setdefault('status', 200)
        kwargs.setdefault('content_type', 'application/json')
        return HttpResponse(content, **kwargs)

    def get_params(self):
        return self.get_json_data()

    def get_json_data(self):
        request = self.request
        limit = self.MAX_CONTENT_SIZE
        content = request.read(limit)
        if not content:
            payload = {}
        else:
            try:
                payload = serializers.decode(content)
            except ValueError:
                raise BadRequest
        return payload
