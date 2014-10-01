
from django.core.paginator import Page, Paginator


class GingerPage(Page):

    def to_json(self):
        pass

class PageLink(object):

    def __init__(self):
        self.url = None
        self.index = None


class GingerPaginator(Paginator):

    parameter_name = "page"

    def __init__(self, *args, **kwargs):
        self.parameter_name = kwargs.get("parameter_name", "page")

    def page_from_request(self):
        pass

    def page_links(self):
        return