from django.http.request import HttpRequest
from django.utils import six
from django.core.paginator import Page, Paginator, EmptyPage, PageNotAnInteger

from ginger import utils
from ginger import ui


__all__ = ["GingerPaginator", "GingerPage", "paginate"]


class GingerPage(Page):

    def create_link(self, request, number):
        base_url = request.get_full_path()
        param = self.paginator.parameter_name
        url = utils.get_url_with_modified_params(request, {param: number})
        return ui.Link(url=url, content=six.text_type(number), is_active=url == base_url)

    def build_links(self, request):
        for i in utils.generate_pages(self.number,
                                      self.paginator.page_limit,
                                      self.paginator.num_pages):
            yield self.create_link(request, i)

    def previous_link(self, request):
        number = self.previous_page_number()
        return self.create_link(request, number)

    def next_link(self, request):
        number = self.next_page_number()
        return self.create_link(request, number)


class GingerPaginator(Paginator):

    parameter_name = "page"
    page_limit = 10
    allow_empty = False

    def __init__(self, object_list, per_page, **kwargs):
        self.parameter_name = kwargs.pop("parameter_name", self.parameter_name)
        self.allow_empty = kwargs.pop("allow_empty", self.allow_empty)
        self.page_limit = kwargs.pop("page_limit", self.page_limit)
        super(GingerPaginator, self).__init__(object_list, per_page, **kwargs)

    def validate_number(self, number):
        """
        Validates the given 1-based page number.
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        if number > self.num_pages:
            if self.allow_empty or (number == 1 and self.allow_empty_first_page):
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number

    def page(self, value):
        """
        Returns a Page object for the given 1-based page number.
        """
        if isinstance(value, HttpRequest):
            value = value.GET.get(self.parameter_name, 1)
        elif isinstance(value, dict):
            value = value.get(self.parameter_name, 1)
        number = self.validate_number(value)
        if number > self.num_pages:
            result = self.object_list.none() if hasattr(self.object_list, "none") else []
        else:
            bottom = (number - 1) * self.per_page
            top = bottom + self.per_page
            if top + self.orphans >= self.count:
                top = self.count
            result = self.object_list[bottom:top]
        return self._get_page(result, number, self)

    def _get_page(self, *args, **kwargs):
        return GingerPage(*args, **kwargs)


def paginate(object_list, page, **kwargs):
    return GingerPaginator(object_list, **kwargs).page(page)