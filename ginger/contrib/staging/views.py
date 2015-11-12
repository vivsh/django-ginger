

from . import conf, forms
from django.shortcuts import redirect
from django.views.generic.base import TemplateView


class StagingView(TemplateView):

    def get_template_names(self):
        return [conf.get("TEMPLATE")]

    def get(self, request, *args, **kwargs):
        context = {
            'form': forms.StagingForm()
        }
        return self.render_to_response(context, status=401)

    def post(self, request, *args, **kwargs):
        session_key = conf.get("SESSION_KEY")
        secret = conf.get("SECRET")
        allowed_hosts = conf.get("ALLOWED_HOSTS")
        form_obj = forms.StagingForm(request.POST)
        host = request.get_host().lower()
        hosts = allowed_hosts

        if (hosts is None or host in hosts) and form_obj.is_valid():
            response = redirect(request.get_full_path())
            response.set_signed_cookie(session_key, secret)
            return response
        else:
            context = {
                'form': form_obj
            }
            return self.render_to_response(context, status=401)


stage = StagingView.as_view()