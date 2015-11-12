
from django.shortcuts import redirect
from ginger.contrib.staging import views
from ginger.contrib.staging import conf


class StagingMiddleware(object):
    
    def process_request(self, request):
        session_key = conf.get("SESSION_KEY")
        secret = conf.get("SECRET")
        value = request.get_signed_cookie(session_key, default=None)
        path_info = request.path_info.strip("/")
        if value != secret:
            return views.stage(request)
        elif path_info == "staging_reset":
            response = redirect("/")
            response.delete_cookie(session_key)
            return response



