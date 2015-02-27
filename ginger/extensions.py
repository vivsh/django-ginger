from jinja2.exceptions import TemplateSyntaxError
from jinja2.ext import Extension
from jinja2 import nodes

from django.conf import settings


class FormExtension(Extension):
    tags = set(['form'])

    def parse(self, parser):
        stream = parser.stream
        lineno = stream.next().lineno

        form_name = parser.parse_expression()
        attrs = []
        while not parser.stream.current.test('block_end'):
            stream.skip_if("comma")
            key = nodes.Const(stream.next().value)
            stream.expect("assign")
            value = parser.parse_expression()
            attrs.append(nodes.Pair(key, value, lineno=lineno))

        body = parser.parse_statements(['name:endform'], drop_needle=True)
        body.insert(0, nodes.Assign(nodes.Name("pappu", 'store'), self.call_method('_make_helper', [form_name])))
        return nodes.CallBlock(
            self.call_method('_render', args=[form_name,
                                              nodes.Dict(attrs),
                                              nodes.Name("csrf_token", "load"),
                                              nodes.Const(lineno)]),
            [], [], body).set_lineno(lineno)

    def _make_helper(self, form):
        from ginger.templatetags.form_tags import FormHelper
        print FormHelper
        return FormHelper(form)

    def _render(self, form_name, attrs, csrf_token, lineno, caller):
        print form_name, attrs, csrf_token
        return caller()


class LoadExtension(Extension):
    tags = set(['load'])

    def parse(self, parser):
        while not parser.stream.current.type == 'block_end':
            parser.stream.next()
        return []


class URLExtension(Extension):
    """Returns an absolute URL matching given view with its parameters.

This is a way to define links that aren't tied to a particular URL
configuration::

{% url path.to.some_view arg1,arg2,name1=value1 %}

Known differences to Django's url-Tag:

- In Django, the view name may contain any non-space character.
Since Jinja's lexer does not identify whitespace to us, only
characters that make up valid identifers, plus dots and hyphens
are allowed. Note that identifers in Jinja 2 may not contain
non-ascii characters.

As an alternative, you may specifify the view as a string,
which bypasses all these restrictions. It further allows you
to apply filters:

{% url "ghg.some-view"|afilter %}
"""

    tags = set(['url'])

    def parse(self, parser):
        stream = parser.stream

        tag = stream.next()

        # get view name
        if stream.current.test('string'):
            # Need to work around Jinja2 syntax here. Jinja by default acts
            # like Python and concats subsequent strings. In this case
            # though, we want {% url "app.views.post" "1" %} to be treated
            # as view + argument, while still supporting
            # {% url "app.views.post"|filter %}. Essentially, what we do is
            # rather than let ``parser.parse_primary()`` deal with a "string"
            # token, we do so ourselves, and let parse_expression() handle all
            # other cases.
            if stream.look().test('string'):
                token = stream.next()
                viewname = nodes.Const(token.value, lineno=token.lineno)
            else:
                viewname = parser.parse_expression()
        else:
            # parse valid tokens and manually build a string from them
            bits = []
            name_allowed = True
            while True:
                if stream.current.test_any('dot', 'sub', 'colon'):
                    bits.append(stream.next())
                    name_allowed = True
                elif stream.current.test('name') and name_allowed:
                    bits.append(stream.next())
                    name_allowed = False
                else:
                    break
            viewname = nodes.Const("".join([b.value for b in bits]))
            if not bits:
                raise TemplateSyntaxError("'%s' requires path to view" %
                    tag.value, tag.lineno)

        # get arguments
        args = []
        kwargs = []
        while not stream.current.test_any('block_end', 'name:as'):
            if args or kwargs:
                stream.expect('comma')
            if stream.current.test('name') and stream.look().test('assign'):
                key = nodes.Const(stream.next().value)
                stream.skip()
                value = parser.parse_expression()
                kwargs.append(nodes.Pair(key, value, lineno=key.lineno))
            else:
                args.append(parser.parse_expression())

        def make_call_node(*kw):
            return self.call_method('_reverse', args=[
                viewname,
                nodes.List(args),
                nodes.Dict(kwargs),
                nodes.Name('_current_app', 'load'),
            ], kwargs=kw)

        # if an as-clause is specified, write the result to context...
        if stream.next_if('name:as'):
            var = nodes.Name(stream.expect('name').value, 'store')
            call_node = make_call_node(nodes.Keyword('fail',
                nodes.Const(False)))
            return nodes.Assign(var, call_node)
        # ...otherwise print it out.
        else:
            return nodes.Output([make_call_node()]).set_lineno(tag.lineno)

    @classmethod
    def _reverse(self, viewname, args, kwargs, current_app=None, fail=True):
        from django.core.urlresolvers import reverse, NoReverseMatch

        # Try to look up the URL twice: once given the view name,
        # and again relative to what we guess is the "main" app.
        url = ''
        try:
            url = reverse(viewname, args=args, kwargs=kwargs,
                current_app=current_app)
        except NoReverseMatch:
            projectname = settings.SETTINGS_MODULE.split('.')[0]
            try:
                url = reverse(projectname + '.' + viewname,
                              args=args, kwargs=kwargs)
            except NoReverseMatch:
                if fail:
                    raise
                else:
                    return ''

        return url

