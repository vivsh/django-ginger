
from django.shortcuts import redirect
from exceptions import ValidationFailure
from ginger.exceptions import Http404
from ginger import utils
from ginger.serializers import process_redirect
from templates import GingerResponse

from django.views.generic import *


class GingerViewMixin(object):

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


class GingerFormView(GingerViewMixin, FormView):

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form_obj = self.get_form(form_class)
        try:
            form_obj.execute()
            return self.form_valid(form_obj)
        except ValidationFailure:
            return self.form_invalid(form_obj)

    def form_valid(self, form):
        url = self.get_success_url()
        return self.redirect(url)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class TwoStepFormView(GingerFormView):

    def get_form_step_context_data(self, form):
        pass

    def get_done_step_context_data(self, data):
        pass

    def is_done_step(self):
        pass

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        if self.is_done_step():
            raise

    def get_context_data(self, **kwargs):
        if self.is_done_step():
            try:
                data = self.request.session[self.session_key]
            except KeyError:
                raise Http404
            return self.get_done_step_context_data(session_data=data)
        else:
            return self.get_form_step_context_data(**kwargs)

    def serialize_data(self, data):
        pass

    def unserialize_data(self, data):
        pass

    def form_valid(self, form):
        result = form.result
        data = self.serialize_data(form)
        self.request.session[self.session_key] = data
        return self.redirect()