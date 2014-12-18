import re



class Num(object):

    def match(self, value):
        return value in {'num', 'int'}

    def pattern(self, value):
        return r'\d+'


class Slug:

    def match(self, value):
        return value == "slug"

    def pattern(self, value):
        return r'[a-z0-9A-Z][a-zA-Z0-9\-]*'


class Name:

    def match(self, value):
        return value == "name"

    def pattern(self, value):
        return r'[a-zA-Z]\w+'


class Choice:

     def match(self, value):
         return value.startswith("(") and value.endswith(")")

     def pattern(self, value):
         parts = value.strip("()").split(",")
         return "|".join(p.strip() for p in parts)


class Pattern(object):

    pattern_types = [Num, Slug, Name, Choice]

    _regex = re.compile("^(\w*)(\?)?:(.+?)(?:\s*\{\s*(\d*)\s*(,\s*\d*)?\s*\})?$")

    def __init__(self, value):
        self.value = value

    def match(self, value):
        for cls in self.pattern_types:
            p = cls()
            if p.match(value):
                return p.pattern(value)
        return value

    def __str__(self):
        return self.create()

    def create(self):
        parts = re.sub("/+", "/", self.value).lstrip("/").split("/")
        result = []
        size = len(parts)
        for i, p in enumerate(parts):
            slash = "" if i == size-1 else "/"
            groups = self._regex.findall(p)
            if not groups:
                if p:
                    p = "%s%s" % (p, slash)
                result.append(p)
            else:
                name, opt, pattern, low, high = groups[0]
                pattern = self.match(pattern)
                if not low and not high:
                    limits = ""
                else:
                    limits = "{%s%s}" % (low, high)
                    limits = re.sub("\s+", "", limits)
                if name:
                    pattern = r"(?P<%s>%s)%s%s" % (name, pattern, limits, slash)
                else:
                    pattern = r"(%s)%s%s" % (pattern, limits, slash)
                if opt:
                    pattern = r"(?:%s)?" % pattern
                result.append(pattern)
        return r"^%s$" % "".join(result)

    def compile(self, **kwargs):
        return re.compile(self.create(), **kwargs)

    def findall(self, text, **kwargs):
        rx = self.compile(**kwargs)
        return rx.findall(text)

    def regex(self):
        return self.create()



if __name__ == "__main__":
    print Pattern("/hello/g/?:(ds|fgfh|fgh|gh){5 ,9}/\d+/").regex()