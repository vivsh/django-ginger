from django.core.urlresolvers import reverse

try:
    from django.utils import six
except ImportError:
    import six
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import (InvalidPage, PageNotAnInteger, EmptyPage)
from django.http import Http404
from django.db import IntegrityError
from django.shortcuts import resolve_url
from ginger import utils


__all__ = [
    "GingerHttpError",
    "IntegrityError", "Http404", "BadRequest", "NotFound",
    "PermissionDenied", "PermissionRequired", "MethodNotFound",
    "LoginRequired", "ValidationError", "ValidationFailure",
    "InvalidPage", "PageNotAnInteger", "EmptyPage",
]


class GingerHttpError(Exception):

    description = None

    def __init__(self, message=None):
        self.description = message if message is not None else self.description
        super(Exception, self).__init__(self.description)

    def to_json(self):
        messages = getattr(settings, "GINGER_HTTP_ERROR_MESSAGES",{})
        class_name = self.__class__.__name__
        return {
            'message': messages.get(class_name, self.description),
            'type': class_name
        }


class BadRequest(GingerHttpError):
    status_code = 400
    description = "Bad Request"


class NotFound(GingerHttpError):
    status_code = 404
    description = "Not Found"


class MethodNotFound(GingerHttpError):
    status_code = 405
    description = "Method not allowed"


class Redirect(GingerHttpError):
    permanent = False

    description = "Content has moved"

    def __init__(self, to, message=None, **kwargs):
        super(Redirect, self).__init__(message)
        self.to = to
        self.kwargs = kwargs

    def create_url(self, request):
        url = resolve_url(self.to, **self.kwargs)
        return url


class PermissionRequired(Redirect):
    status_code = 401
    description = "Permission Required"

    def __init__(self, url, message=None):
        super(PermissionRequired, self).__init__(url, message=message)

    def create_url(self, request):
        current_url = request.get_full_path()
        url = utils.get_url_with_modified_params(self.to, {"next": current_url})
        return url


class LoginRequired(PermissionRequired):

    def __init__(self, message=None):
        url = reverse("login")
        super(LoginRequired, self).__init__(url, message=message)

    def create_url(self, request):
        current_url = request.get_full_path()
        url = utils.get_url_with_modified_params(self.to, {"next": current_url})
        return url


class ValidationFailure(GingerHttpError):
    status_code = 422

    def __init__(self, form):
        super(ValidationFailure, self).__init__()
        self.form = form

    def to_json(self):
        data = super(ValidationFailure, self).to_json()
        errors = self.form.errors
        func = getattr(self.form, 'get_failure_message', None)
        if func:
            data['message'] = func()
        data['data'] = {f: e.get_json_data(False) for f, e in errors.items()}
        return data

