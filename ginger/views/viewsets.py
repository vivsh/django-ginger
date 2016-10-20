from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect
from ginger.paginator import GingerPaginator
from .base import GingerViewSetMixin, view
from .generic import *


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
    def detail(self, request, object_id):
        self.object = self.get_object()
        context = self.get_context_data(**{self.context_object_key:self.object})
        return self.render_to_response(context)


class CreateViewSetMixin(object):

    @view(many=True)
    def create(self, request):
        return self.handle_object_form(request)


class UpdateViewSetMixin(object):

    @view
    def update(self, request, object_id):
        self.object = self.get_object()
        return self.handle_object_form(request)


class DeleteViewSetMixin(object):

    @view
    def delete(self, request, object_id):
        self.object = self.get_object()
        return self.handle_object_form(request)


class ListViewSetMixin(object):

    context_page_key = 'page_obj'

    @view(many=True, suffix="")
    def list(self, request):
        object_list = self.filter_queryset(self.get_queryset())

        ctx = {}

        object_list = self.paginate_queryset(object_list)
        ctx[self.context_page_key] = object_list

        if self.table_class:
            object_list = self.table_class(object_list)

        ctx[self.context_object_list_key] = object_list

        return self.render_to_response(self.get_context_data(**ctx))


class GingerModelViewSet(GingerViewSetMixin, GingerFormView):

    filter_class = None
    table_class = None
    paginator = GingerPaginator
    context_object_list_key = 'object_list'
    params_page_key = 'page'
    per_page = None

    def get_queryset(self):
        pass

    def filter_queryset(self, queryset):
        if self.filter_class:
            request = self.request
            form = self.filter_class(data=request.GET, files=request.FILES)
            queryset = form.perform_filter()
        return queryset

    def paginate_queryset(self, queryset):
        if not self.per_page:
            return queryset
        return self.paginator(queryset, per_page=self.per_page, parameter_name=self.params_page_key, allow_empty=False).page(self.request)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            obj = queryset.get(pk=self.kwargs['object_id'])
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
        return getattr(self, 'object', None)

    def get_filter_form(self):
        return self.filter_class

    def handle_object_form(self, request):
        method = request.method
        if method == 'GET':
            form = self.get_form(None, data=None, files=None)
            return self.render_form(form)
        else:
            return self.process_submit(None, data=request.POST, files=request.FILES)

    def handle_queryset_action(self, request):
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