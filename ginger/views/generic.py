from django.views.generic.base import TemplateResponseMixin
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from ginger.exceptions import ValidationFailure
from ginger.exceptions import Http404
from ginger import utils
from ginger.serializers import process_redirect
from ginger.templates import GingerResponse

from django.views.generic import *


class GingerView(View):

    response_class = GingerResponse

    def is_ajax(self):
        return self.request.is_ajax()

    def redirect(self, to, **kwargs):
        response = redirect(to, **kwargs)
        if self.is_ajax():
            status, content = process_redirect(self.request, response)
            return self.render_to_response(content,
                                           status=status,
                                           content_type="application/json")
        else:
            return response

    @classmethod
    def class_oid(cls):
        return utils.create_hash(utils.qualified_name(cls))

    def _get_session_key(self):
        return self.class_oid()

    @property
    def session_key(self):
        return self._get_session_key()

    def get_context_data(self, **kwargs):
        return kwargs


class GingerTemplateView(GingerView, TemplateResponseMixin):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class GingerFormView(GingerView, TemplateResponseMixin):

    def get_form_class(self):
        return self.form_class

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return self.process_form(form_class, request.POST, request.FILES)

    def form_valid(self, form):
        url = self.get_success_url()
        return self.redirect(url)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_form_initial(self):
        return {}

    def get_form_prefix(self):
        return

    def get_form_kwargs(self):
        kwargs = {
            "initial": self.get_form_initial(),
            "prefix": self.get_form_prefix(),
        }
        if hasattr(self, 'object'):
            kwargs.update({'instance': self.object})
        return kwargs

    def process_form(self, form_class, data=None, files=None):
        form_obj = self.get_form(form_class, data, files)
        try:
            form_obj.run()
            return self.form_valid(form_obj)
        except ValidationFailure:
            return self.form_invalid(form_obj)

    def get_form(self, form_class, data, files):
        kwargs = self.get_form_kwargs()
        kwargs['data'] = data
        kwargs['files'] = files
        form_obj = form_class(**kwargs)
        return form_obj


class GingerSearchView(GingerFormView):

    per_page = None
    page_parameter_name = "page"
    page_limit = 10

    def get_form_kwargs(self):
        ctx = super(GingerSearchView, self).get_form_kwargs()
        ctx["parameter_name"] = self.page_parameter_name
        ctx["page_limit"] = self.page_limit
        ctx["per_page"] = self.per_page
        ctx["page"] = self.request
        return ctx

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return self.process_form(form_class, request.GET, request.FILES)

    def post(self, request, *args, **kwargs):
        return redirect(request.get_full_path())

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class FormDoneView(GingerFormView):

    done_step = "done"

    def get_form_step_context_data(self, **kwargs):
        return kwargs

    def get_done_step_context_data(self, **kwargs):
        return kwargs

    def is_done_step(self):
        return self.done_step == self.kwargs.get('step')

    def get_done_url(self):
        match = self.request.resolver_match
        params = self.kwargs.copy()
        params['step'] = self.done_step
        return reverse(match.url_name, args=self.args, kwargs=params)

    def get_done_template_name(self):
        file_name, ext = os.path.splitext(self.template_name)
        return "%s_%s%s" % (file_name, self.done_step, ext)
    
    def get_template_names(self):
        templates = super(FormDoneView, self).get_template_names()
        if self.is_done_step():
            return self.get_done_template_name()
        return templates

    def post(self, request, *args, **kwargs):
        if self.is_done_step():
            raise Http404
        return super(FormDoneView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.is_done_step():
            try:
                value = self.request.session[self.session_key]
            except KeyError:
                raise Http404
            else:
                data = self.unserialize_data(value)
                return self.get_done_step_context_data(object=data, **kwargs)
        else:
            return self.get_form_step_context_data(**kwargs)

    def serialize_data(self, data):
        return data

    def unserialize_data(self, data):
        return data

    def form_valid(self, form):
        result = form.result
        data = self.serialize_data(result)
        self.request.session[self.session_key] = data
        return self.redirect(self.get_done_url())

