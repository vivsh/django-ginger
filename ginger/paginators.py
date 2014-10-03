
from collections import namedtuple
from django.core.paginator import Page, Paginator

from ginger import utils

__all__ = ["GingerPaginator"]


class PageLink(object):

    def __init__(self, page, index):
        self.page = page
        self.index = index
        self.is_active = page.number == index

    @property
    def url(self):
        request = self.page.request
        name = self.page.parameter_name
        return utils.get_url_with_modified_params(request, {name: self.index})


class GingerPage(Page):

    @property
    def page_links(self):
        for i in utils.generate_pages(self.number,
                                      self.paginator.page_limit,
                                      self.paginator.count):
            yield PageLink(self, i)


class GingerPaginator(Paginator):

    parameter_name = "page"
    page_limit = 10

    def __init__(self, object_list, per_page, **kwargs):
        self.parameter_name = kwargs.pop("parameter_name", self.parameter_name)
        self.page_limit = kwargs.pop("page_limit", self.page_limit)
        super(GingerPaginator, self).__init__(object_list, per_page, **kwargs)

    def page(self, request):
        num = request.GET.get(self.parameter_name, 1)
        page_obj = super(GingerPaginator, self).page(num)
        page_obj.parameter_name = self.parameter_name
        page_obj.request = request
        return page_obj

    def _get_page(self, *args, **kwargs):
        return GingerPage(*args, **kwargs)
