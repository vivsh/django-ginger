
from ginger import template


registry = template.Library()


class NavItem(object):
    
    is_used = False
    
    def __init__(self, kwargs):
        for k,v in kwargs.iteritems():
            setattr(self, k, v)


@registry.tag(takes_context=True)
def ginger_nav(context, menu):
    """
    The longest match is considered to be the correct match
    """
    request = context["request"]
    path = request.path_info
    items = []
    match_len = 0
    for item in menu:
        mi = NavItem(item) 
        if mi.url == path or path.startswith(mi.url):
            if match_len < len(mi.url):
                for ni in items:
                    ni.is_used = False
                mi.is_used = True
                match_len = len(mi.url)
        items.append(mi)
    return items    
            