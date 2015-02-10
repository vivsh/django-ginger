
from django.utils.text import mark_safe as make_safe
from django_jinja import library
import functools
import jinja2

__all__ = ['Library']

class Library(library.Library):
    
    def tag(self, template=None,name=None,takes_context=False, mark_safe=False):
        def closure(orig_func):      
            func = orig_func
            name_ = name or getattr(func,'_decorated_function',func).__name__ 
            if template:
                def wrapper(*args,**kwargs):
                    from django_jinja.base import env                
                    t = env.get_template(template)
                    values = orig_func(*args,**kwargs)                                                                                       
                    result = t.render( values )
                    if mark_safe:
                        result = jinja2.Markup(result)
                    return result
                func = functools.update_wrapper(wrapper, func)
            elif mark_safe:
                def wrapper(*args, **kwargs):
                    result = orig_func(*args, **kwargs)
                    return jinja2.Markup(result)
                func = functools.update_wrapper(wrapper, func)
            if takes_context:
                func = jinja2.contextfunction(func)
            self.global_function(name_, func)
            return orig_func
        return closure
    
        