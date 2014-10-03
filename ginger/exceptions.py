from django.utils.html import escape

try:
    from django.utils import six
except ImportError:
    import six
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import (InvalidPage, PageNotAnInteger, EmptyPage)
from django.http import Http404
from django.db import IntegrityError

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
        return {'message': self.description, 'type': self.__class__.__name__}


class BadRequest(GingerHttpError):
    status_code = 400
    description = "Bad Request"


class NotFound(GingerHttpError):
    status_code = 404
    description = "Not Found"


class MethodNotFound(GingerHttpError):
    status_code = 405
    description = "Method not allowed"


class PermissionRequired(GingerHttpError):
    status_code = 401
    description = "Permission Required"


class LoginRequired(PermissionRequired):
    pass


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

