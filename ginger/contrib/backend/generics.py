from django.core.urlresolvers import reverse
from django.http.response import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import *
from ginger import views, serializer
from ginger.views.viewsets import *
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from ginger.exceptions import MethodNotFound, BadRequest, Redirect
import logging


__all__ = ['BackendModelViewSet', 'BackendViewSet', 'ListViewSetMixin', 'CreateViewSetMixin',
           'DeleteViewSetMixin', 'DetailViewSetMixin', 'UpdateViewSetMixin']


logger = logging.getLogger(__name__)


class BackendViewMixin(object):

    site = None


class BackendViewSet(BackendViewMixin, views.GingerViewSet):
    pass


class BackendModelViewSet(BackendViewMixin, views.GingerModelViewSet):
    pass

