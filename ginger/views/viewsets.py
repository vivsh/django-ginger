from django.conf import settings
from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect
from ginger.paginator import GingerPaginator
from .base import GingerViewSetMixin, view
from .generic import *
import logging


__all__ = ['GingerViewSet',
           'CreateViewSetMixin',
           'GingerModelViewSet',
           'UpdateViewSetMixin',
           'ListViewSetMixin',
           'DeleteViewSetMixin',
           'DetailViewSetMixin'
           ]



class GingerViewSet(GingerViewSetMixin, GingerTemplateView):
    pass


class DetailViewSetMixin(object):

    @view(suffix="")
    def detail(self, request):
        self.object = self.get_object()
        ctx = {
            self.context_object_key: self.object
        }
        if self.object_formatter:
            ctx[self.context_formatted_object_key] = self.object_formatter(self.object)
        context = self.get_context_data(**ctx)
        return self.render_to_response(context)


class CreateViewSetMixin(object):

    @view(many=True)
    def create(self, request):
        return self.handle_object_form()


class UpdateViewSetMixin(object):

    @view
    def update(self, request):
        self.object = self.get_object()
        return self.handle_object_form()


class DeleteViewSetMixin(object):

    @view
    def delete(self, request):
        self.object = self.get_object()
        return self.handle_object_form()


class ListViewSetMixin(object):

    context_page_key = 'page_obj'

    @view(many=True, suffix="")
    def list(self, request):
        object_list = self.filter_queryset(self.get_queryset())

        ctx = {}

        object_list = self.paginate_queryset(object_list)
        ctx[self.context_page_key] = object_list

        if self.object_list_formatter:
            object_list = self.object_list_formatter(object_list)

        ctx[self.context_object_list_key] = object_list

        ctx['filter_form'] = self.filter_form

        return self.render_to_response(self.get_context_data(**ctx))


class GingerModelViewSet(GingerViewSetMixin, GingerFormView):

    filter_class = None

    object_formatter = None
    object_list_formatter = None

    paginator = GingerPaginator
    url_object_key = 'object_id'
    context_object_list_key = 'object_list'
    context_formatted_object_key = 'formatted_object'
    params_page_key = 'page'
    per_page = None

    OK_BACK = 1
    YES_BACK = 2
    CONFIRM_BACK = 3
    SUBMIT_BACK = 4

    def get_queryset(self):
        raise NotImplementedError

    def filter_queryset(self, queryset):
        filter_class = self.get_filter_class()
        self.filter_form = self.get_filter_form(queryset)
        if self.filter_form:
            queryset = self.filter_form.perform_filter()
        return queryset

    def get_filter_kwargs(self, queryset):
        return {
            "initial": self.get_filter_initial(),
            "queryset": queryset,
            "data": self.request.GET,
            "files": None
        }

    def get_filter_initial(self):
        return None

    def get_filter_form(self, queryset):
        filter_class = self.get_filter_class()
        if filter_class:
            request = self.request
            kwargs = self.get_filter_kwargs(queryset)
            return filter_class(**kwargs)

    def paginate_queryset(self, queryset):
        if not self.per_page:
            return queryset
        return self.paginator(queryset, per_page=self.per_page, parameter_name=self.params_page_key, allow_empty=False).page(self.request)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            obj = queryset.get(pk=self.kwargs[self.url_object_key])
            self.check_object_permissions(obj)
            return obj
        except queryset.model.DoesNotExist:
            raise Http404

    def get_form_context(self, form_key):
        ctx = super(GingerModelViewSet, self).get_form_context(form_key)
        ctx['request'] = self.request
        ctx['action'] = self.action
        return ctx

    def get_form_instance(self, form_key):
        return getattr(self, self.context_object_key, None)

    def get_filter_class(self):
        return self.filter_class

    def render_context(self, context):
        return self.render_to_response(self.get_context_data(**context))

    def handle_object_action(self):
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        self.template_name = "backend/object_action.html"
        return self.handle_object_form()

    def handle_object_form(self):
        request = self.request
        method = request.method
        if method == 'GET':
            form = self.get_form(None, data=None, files=None)
            return self.render_form(form)
        else:
            if self.success_url is None:
                if self.action in {'delete', "create"}:
                    self.success_url = self.reverse('list')
                else:
                    self.success_url = self.reverse('detail', object_id=self.object.id)
            return self.process_submit(None, data=request.POST, files=request.FILES)

    def handle_queryset_action(self):
        request = self.request
        method = request.method
        if method == 'GET':
            return HttpResponse("Bad Request", status=400)
        else:
            object_list = self.get_queryset()
            form = self.filter_class(queryset=object_list, action=self.action, data=request.GET)
            if form.is_valid():
                return redirect(self.get_success_url(form))
            else:
                return redirect(self.get_previous_url())