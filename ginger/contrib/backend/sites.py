
from django.conf.urls import include, url
from ginger.utils import iter_app_modules


__all__ = ['BackendModule', 'BackendSite']



class BackendModule(object):
    label = ""
    icon = ""

    def __init__(self, name):
        self.name = name

    def get_views(self):
        raise NotImplementedError


class BackendSite(object):

    def __init__(self, module_name):
        self.name = module_name
        self.modules = []

    def register(self, module):
        self.modules.append(module)

    def discover(self):
        for _ in iter_app_modules(self.name, deep=False):
            pass

    @property
    def urls(self):
        url_patterns = []
        for module in self.modules:
            name = module.name
            views = module.get_views()
            module_urls = []
            for view in views:
                if hasattr(view, 'as_urls'):
                    module_urls.extend(view.as_urls(site=self))
                else:
                    module_urls.append(view.as_url(site=self))
            url_patterns.append(url("^%s/" % name, include(module_urls)))
        return url_patterns

