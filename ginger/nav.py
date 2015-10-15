
from collections import OrderedDict

__all__ = ["Link"]


class Link(object):

    def __init__(self, content, icon=None, url=None, **kwargs):
        self.content = content
        self.icon = icon
        self.url = url
        self.children = OrderedDict()
        self.is_active = False
        self.is_open = True
        for k,v in kwargs.items():
            setattr(self, k, v)

    def set_active(self, url):
        self.is_open = self.is_active = url == self.url
        for n in self:
            n.set_active(url)
        if not self.is_open:
            self.is_open = any(n.is_open for n in self)

    def __iter__(self):
        return iter(self.children.values())

    @property
    def is_leaf(self):
        return not self.children

    def add(self, content, url=None, **kwargs):
        kwargs['url'] = url
        child = Link(content, **kwargs)
        self.children[content] = child
        return child

    def __getitem__(self, item):
        return self.children[item]

    def __contains__(self, item):
        return item in self.children

    def __len__(self):
        return len(self.children)

    def child(self, path):
        fragments = path.split("/")
        folder = self
        for f in fragments:
            if f not in folder:
                folder.add(f)
            folder = folder[f]
        return folder

    def render_children(self):
        if self.children:
            return "<ul>%s</ul>"%("".join(n.render("li") for n in self),)
        else:
            return ""

    def render(self, tag="div"):
        return "<%s><a href='%s'>%s</a>%s</%s>" % (tag, self.url, self.content, self.render_children(), tag)

    def build_links(self, request):
        path_info = request.path_info
        self.set_active(path_info)
        return [self]


if __name__ == '__main__':
    root = Link("Hello")
    child = root.child("Some/Things/Should/Not/Be/Seen")
    print(root.render())
