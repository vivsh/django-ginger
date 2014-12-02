

class Resource(object):

    def __init__(self, singular, plural, app_name, pattern, collection=False):
        self.singular = singular
        self.plural = plural
        self.app_name = app_name
        self.pattern = pattern or self.plural
        self.is_collection = collection
        self.actions = []

    @property
    def name(self):
        return self.singular

    def get_url_name(self):
        """
        Name that will be used in url construction
        """
        return self.name

    def get_url_pattern(self):
        """
        """
        return self.pattern

    def get_template_name(self):
        """
        Name that will be used in template_name construction
        """
        return self.name

    def get_form_name(self):
        """
        Name for form name construction
        """
        return self.name

    def add_action(self, action):
        self.actions.append(action)

    def get_actions(self):
        return self.actions



class Verb(object):

    name = None

    def get_template_name(self, resource):
        return "%s/%s_%s.html" % (resource.app_name, resource.get_template_name(), self.name)

    def get_form_name(self, resource):
        parts = [resource.get_form_name(), self.name, "form"]
        return "".join(p.capitalize() for p in parts)

    def get_url_name(self, resource):
        return "%s_%s" % (resource.get_url_name(), self.name)

    def get_url_pattern(self, resource):
        return r"^%s/%s/$" % (resource.get_url_pattern(), self.name)


class Get(Verb):
    name = "detail"

    def get_template_name(self, resource):
        return "detail" if not resource.is_collection else ""

    def get_url_pattern(self, resource):
        return r"^%s/%s/$" % (resource.get_url_pattern(), self.name)


class New(Verb):
    name = "new"


class Delete(Verb):
    name = "delete"


class Edit(Verb):
    name = "edit"


class ResourceVerb(object):

    def __init__(self, resource, verb):
        self.resource = resource
        self.verb = verb

    def get_template_name(self):
        return self.verb.get_template_name(self.resource)

    def get_form_name(self):
        parts = [self.resource.get_form_name(), self.verb.get_form_name(), "form"]
        return "".join(a.capitalize() for a in parts)

    def get_url_name(self):
        parts = [self.resource.get_url_name(), self.verb.get_url_name(), "form"]
        return "/".join(a.lower() for a in parts)

    def get_template_content(self):
        return


if __name__ == '__main__':
    user = Resource("User")
    user.add_verb(Get())

