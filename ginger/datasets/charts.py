from ginger.utils import get_url_with_modified_params


class UITable(object):


    def __init__(self, dataset):
        self.dataset = dataset

    def cell_css_class(self, value, row, column):
        pass

    def table_css_class(self):
        pass

    def row_css_class(self, row):
        pass

    def build_links(self, request):
        data = request.GET
        sort_name = getattr(self, "sort_parameter_name", None)
        for col in self.columns.visible():
            if sort_name:
                field = self.sort_field
                code = field.get_value_for_name(col.name)
                value = data.get(sort_name, "")
                reverse = value.startswith("-")
                if reverse:
                    value = value[1:]
                is_active = code == value
                next_value = "-%s" % code if not reverse and is_active else code
                mods = {sort_name: next_value}
            else:
                is_active = False
                reverse = False
                mods = {}
            url = get_url_with_modified_params(request, mods)
            link = ui.Link(content=col.label, url=url, is_active=is_active, reverse=reverse)
            yield link

    def render(self, context, **kwargs):
        return



class UIBarChart(object):

    def __init__(self, dataset, xaxis=(),y_axis=()):
        self.dataset = dataset

    name = Axis('x')

    def get_series(self):
        return

    def get_axes(self):
        return


class UIBarChart(object):
    pass