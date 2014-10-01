
from django.views.generic import DetailView


class DetailView(DetailView):

    def check_access(self, request):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.check_access(request)
        return super(DetailView, self).dispatch(request, *args, **kwargs)