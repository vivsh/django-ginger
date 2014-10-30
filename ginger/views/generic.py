
import os
from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.utils.functional import cached_property
from django.views.generic.base import TemplateResponseMixin, View
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from ginger.exceptions import ValidationFailure
from ginger.exceptions import Http404
from ginger import utils
from ginger.serializer import process_redirect
from ginger.templates import GingerResponse

from . import storages, steps


__all__ = ['GingerView', 'GingerTemplateView', 'GingerSearchView',
           'GingerDetailView', 'GingerFormView', 'GingerWizardView',
           'GingerFormDoneView']


class GingerSessionDataMixin(object):

    def get_session_key(self):
        host = self.request.get_host()
        return "%s-%s" % (host, self.class_oid())

    def get_session_data(self):
        return self.request.session.get(self.get_session_key())

    def set_session_data(self, data):
        self.request.session[self.get_session_key()] = data

    @classmethod
    def class_oid(cls):
        return utils.create_hash(utils.qualified_name(cls))


class GingerView(View, GingerSessionDataMixin):

    user = None

    def get_user(self):
        return self.request.user

    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user()
        return super(GingerView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if 'view' not in kwargs:
            kwargs['view'] = self
        return kwargs




class GingerTemplateView(GingerView, TemplateResponseMixin):

    response_class = GingerResponse

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def redirect(self, to, **kwargs):
        response = redirect(to, **kwargs)
        if self.request.is_ajax():
            status, content = process_redirect(self.request, response)
            return self.render_to_response(content,
                                           status=status,
                                           content_type="application/json")
        else:
            return response


class GingerDetailView(GingerTemplateView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object, **kwargs)
        return self.render_to_response(context)


class GingerFormView(GingerTemplateView):

    def get_success_url(self, form_class):
        return self.success_url

    def get_form_class(self, form_key=None):
        return self.form_class

    def get_form_key(self):
        return

    def can_submit(self):
        return self.request.method == "POST"

    def post(self, request, *args, **kwargs):
        if self.can_submit():
            return self.process_submit(
                form_key=self.get_form_key(),
                data=request.POST,
                files=request.FILES
            )
        return self.redirect(request.get_full_path())

    def get(self, request, *args, **kwargs):
        if self.can_submit():
            return self.process_submit(form_key=self.get_form_key(), data=request.GET)
        form = self.get_form(form_key=self.get_form_key())
        context = self.get_context_data(form=form, **kwargs)
        return self.render_to_response(context)

    def form_valid(self, form):
        url = self.get_success_url()
        return self.redirect(url)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_form_initial(self, form_key):
        return

    def get_form_prefix(self, form_key):
        return

    def get_form_instance(self, form_key):
        return

    def get_form_kwargs(self, form_key):
        kwargs = {
            "initial": self.get_form_initial(form_key),
            "prefix": self.get_form_prefix(form_key),
        }
        form_class = self.get_form_class(form_key)
        if form_class and issubclass(form_class, ModelForm):
            kwargs['instance'] = self.get_form_instance(form_key)
        return kwargs

    def process_submit(self, form_key, data=None, files=None):
        form_obj = self.get_form(form_key, data=data, files=files)
        try:
            form_obj.run()
            return self.form_valid(form_obj)
        except ValidationFailure:
            return self.form_invalid(form_obj)

    def get_form(self, form_key, data=None, files=None):
        form_class = self.get_form_class(form_key)
        kwargs = self.get_form_kwargs(form_key)
        kwargs['data'] = data
        kwargs['files'] = files
        form_obj = form_class(**kwargs)
        return form_obj


class GingerSearchView(GingerFormView):

    per_page = None
    page_parameter_name = "page"
    page_limit = 10

    def get_form_kwargs(self, form_key):
        ctx = super(GingerSearchView, self).get_form_kwargs(form_key)
        ctx["parameter_name"] = self.page_parameter_name
        ctx["page_limit"] = self.page_limit
        ctx["per_page"] = self.per_page
        ctx["page"] = self.request
        return ctx

    def can_submit(self):
        return self.request.method == 'GET'

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class GingerStepViewMixin(object):

    step_parameter_name = "step"
    done_step = "done"

    def commit(self, form_data):
        raise NotImplementedError

    def get_step_names(self):
        raise NotImplementedError

    def get_form_key(self):
        return self.current_step_name()


    def current_step_name(self):
        return self.kwargs.get(self.step_parameter_name)

    def get_step_url(self, step_name):
        match = self.request.resolver_match
        params = self.kwargs.copy()
        params.pop(self.step_parameter_name, None)
        if step_name is not None:
            params[self.step_parameter_name] = step_name
        return reverse(match.url_name, args=tuple(self.args), kwargs=params)

    def get_done_url(self):
        return self.get_step_url(self.done_step)

    def process_commit(self):
        raise NotImplementedError

    def render_done(self):
        data = self.get_session_data()
        if data is None:
            response = self.process_commit()
            if response:
                return response
        kwargs = self.kwargs.copy()
        if data:
            kwargs.update(data)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def is_done_step(self):
        return self.current_step_name() == self.done_step and self.request.method == 'GET'

    def dispatch(self, request, *args, **kwargs):
        step_name = self.current_step_name()
        step_names = self.get_step_names()
        if step_name is None:
            if step_names:
                return self.redirect(self.get_step_url(step_names[0]))
        elif step_name not in step_names and not self.is_done_step():
            raise Http404
        return super(GingerStepViewMixin, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        step_name = self.current_step_name()
        method = getattr(self, "process_%s_step" % step_name, None)
        if method:
            response = method()
            if response:
                return response
        if self.is_done_step():
            return self.render_done()
        return super(GingerStepViewMixin, self).get(request, *args, **kwargs)


class GingerFormDoneView(GingerStepViewMixin, GingerFormView):

    def get_step_names(self):
        return ()

    def process_commit(self):
        return self.redirect(self.get_step_url(None))

    def form_valid(self, form):
        result = form.result
        self.set_session_data(result)
        return self.redirect(self.get_done_url())

    def get_template_names(self):
        if self.is_done_step():
            base, ext = os.path.splitext(self.template_name)
            return ["%s_%s%s" % (base, self.done_step, ext)]
        else:
            return [self.template_name]


class GingerWizardView(GingerStepViewMixin, GingerFormView):

    template_format = None
    file_upload_dir = "tmp/"
    form_storage_class = storages.SessionFormStorage

    def __init__(self, *args, **kwargs):
        super(GingerWizardView, self).__init__(*args, **kwargs)
        self.file_storage = self.get_file_storage()
        self.steps = steps.StepList(self)

    @cached_property
    def form_storage(self):
        return self.get_form_storage()

    def get_form_storage(self):
        return self.form_storage_class(self)

    def get_file_storage(self):
        location = self.file_upload_dir or getattr(settings, "TEMP_MEDIA_DIR", "tmp")
        return FileSystemStorage(os.path.join(settings.MEDIA_ROOT, location))

    def get_template_names(self):
        if self.template_format is None:
            raise ImproperlyConfigured("template_format cannot be None in %r" % self.__class__)
        step_name = self.current_step_name()
        return self.template_format % {"step": step_name}

    def get_form_class(self, form_key=None):
        step_name = form_key
        if step_name is None:
            step_name = self.current_step_name()
        return self.steps[step_name].get_form_class()

    def get_next_url(self):
        step = self.steps.next()
        return step.url if step else self.get_done_url()

    def form_valid(self, form):
        step_name = self.current_step_name()
        self.form_storage.set(step_name, form.data, form.files)
        url = self.get_next_url()
        return self.redirect(url)

    def process_commit(self):
        form_data = {}
        for step_name in self.get_step_names():
            form_obj = self.validate_step(step_name)
            step = self.steps[step_name]
            if not form_obj.is_valid() and (not step.can_skip or form_obj.is_bound):
                return self.redirect(self.get_step_url(step_name))
            form_data.update(form_obj.cleaned_data)
        data = self.commit(form_data)
        self.set_session_data(data)
        self.form_storage.clear()

    def get_step_names(self):
        return self.steps.names()

    def commit(self, form_data):
        return {}

    def get_cleaned_data_for_step(self, step_name):
        return self.validate_step(step_name).cleaned_data

    def get_cleaned_data(self, step_names=None):
        result = {}
        for form_obj in self.validate_step(step_names):
            data = form_obj.cleaned_data
            result.update(data)
        return result

    def can_submit(self):
        method = self.steps.current.method
        request = self.request
        if request.method == "POST" or (method == "GET" and request.method == "GET" and request.GET):
            return True
        return False

    def validate_step(self, step_name):
        data, files = self.form_storage.get(step_name)
        form_obj = self.get_form(step_name, data, files)
        form_obj.step_name = step_name
        try:
            if hasattr(form_obj, "run"):
                form_obj.run()
        except ValidationFailure:
            pass
        return form_obj

    def validate_steps(self, step_names=None):
        if step_names is None:
            step_names = self.get_step_names()
        for step_name in step_names:
            yield self.validate_step(step_name)

    @classmethod
    def delete_old_files(cls, **kwargs):
        wiz = cls()
        expired = timezone.now() - timedelta(**kwargs)
        file_storage = wiz.get_file_storage()
        try:
            files = file_storage.listdir("")[-1]
        except OSError:
            return
        for filename in files:
            access_time = file_storage.accessed_time(filename)
            if access_time < expired:
                file_storage.delete(filename)


