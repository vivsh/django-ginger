from django.http.request import HttpRequest
from django.utils import six
from django.core.paginator import Page, Paginator

from ginger import utils
from ginger import ui


__all__ = ["GingerPaginator", "GingerPage"]


class GingerPage(Page):

    def build_links(self, request):
        base_url = request.get_full_path()
        param = self.paginator.parameter_name
        for i in utils.generate_pages(self.number,
                                      self.paginator.page_limit,
                                      self.paginator.count):
            url = utils.get_url_with_modified_params(request, {param: i})
            yield ui.Link(url, six.text_type(i), url==base_url)


class GingerPaginator(Paginator):

    parameter_name = "page"
    page_limit = 10

    def __init__(self, object_list, per_page, **kwargs):
        self.parameter_name = kwargs.pop("parameter_name", self.parameter_name)
        self.page_limit = kwargs.pop("page_limit", self.page_limit)
        super(GingerPaginator, self).__init__(object_list, per_page, **kwargs)

    def page(self, value):
        if isinstance(value, (int, six.text_type)):
            num = int(value)
        elif isinstance(value, HttpRequest):
            num = value.GET.get(self.parameter_name, 1)
        else:
            num = value.get(self.parameter_name, 1)
        page_obj = super(GingerPaginator, self).page(num)
        return page_obj

    def _get_page(self, *args, **kwargs):
        return GingerPage(*args, **kwargs)
