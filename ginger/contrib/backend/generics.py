from django.core.urlresolvers import reverse
from django.http.response import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import *
from ginger import views, serializer
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from ginger.exceptions import MethodNotFound, BadRequest, Redirect
import logging


__all__ = ['BackendModelViewSet', 'BackendViewSet']


logger = logging.getLogger(__name__)


class BackendViewMixin(object):

    site = None

    permission_classes = []

    side_menu = False

    top_menu = False

    def process_request(self, request):
        user = self.user = self.get_user()
        if not user.is_authenticated() or not user.is_staff:
            raise Redirect(reverse("Backend:login")+"?next=%s" % request.get_full_path())


class BackendViewSet(BackendViewMixin, views.GingerViewSet):
    pass


class BackendModelViewSet(BackendViewMixin, views.GingerModelViewSet):
    pass

