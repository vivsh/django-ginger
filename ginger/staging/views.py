
from . import conf, forms
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView


class StagingView(TemplateView):

    template_name = conf.STAGING_TEMPLATE

    def get(self, request, *args, **kwargs):
        context = {
            'form': forms.StagingForm()
        }
        return self.render_to_response(context, status=401)

    def post(self, request, *args, **kwargs):
        form_obj = forms.StagingForm(request.POST)
        host = request.get_host().lower()
        hosts = conf.STAGING_ALLOWED_HOSTS

        if (hosts is None or host in hosts) and form_obj.is_valid():
            response = redirect(request.get_full_path())
            response.set_signed_cookie(conf.STAGING_SESSION_KEY, conf.STAGING_SECRET)
            return response
        else:
            context = {
                'form': form_obj
            }
            return self.render_to_response(context, status=401)


stage = StagingView.as_view()