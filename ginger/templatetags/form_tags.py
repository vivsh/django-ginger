
import json
import re
from ginger.templates import ginger_tag
from ginger import utils as gutils

from django.template.loader import render_to_string
from django.middleware.csrf import get_token
from django.conf import settings



def make_css_class(*classes):
    result = []
    history = set()
    for c in classes:
        parts = re.split(r'\s+',c)
        for part in parts:
            if part and part not in history:
                result.append(part)
                history.add(part)
    return ' '.join(result)


def make_attrs(attrs):
    result = []
    css = []
    for k, v in attrs.iteritems():
        if k == 'class':
            css.append(v)
            continue
        if isinstance(v, basestring):
            v = str(v).encode('string-escape')
        else:
            v = json.dumps(v)
        result.append("%s='%s'"% (k,v))
    css = make_css_class(*css)
    if css:
        result.append("class=%s" % css)
    return " ".join(result)

                        
def get_form_attrs(form,**kwargs):
    attrs = kwargs.copy()
    attrs['method'] = kwargs.pop('method','post')
    attrs['enctype']='multipart/form-data' if form.is_multipart() else 'application/x-www-form-urlencoded'
    css = kwargs.get("class","")
    prefix =  get_css_prefix()
    css = "%sform %sform-horizontal %s"%(prefix, prefix, css)
    attrs['class'] = css.strip()
    return make_attrs(attrs)


def create_submit_tag(form,**kwargs): 
    attrs = kwargs.copy()
    attrs.setdefault('class','btn btn-primary')
    attrs.setdefault('name', gutils.get_form_submit_name(form))
    attrs.setdefault('value', 'submit')
    attrs.update({'type': 'submit'})   
    label = attrs.pop('label', 'Save') 
    attrs = make_attrs(attrs)
    return "<button %s> %s </button>"% (attrs, label)


def create_form_tag(form,**kwargs):
    return "<form %s > %s"% (get_form_attrs(form,**kwargs), form.non_field_errors()) 


def create_csrf_tag(context):      
    request = context["request"]
    csrf_token = context.get('csrf_token',get_token(request))
    if not csrf_token: raise Exception("No csrf token provided in the context")
    return "<div style='display:none'><input type='hidden' name='csrfmiddlewaretoken' value='%s' /></div>" % (csrf_token,)        


@ginger_tag(mark_safe=True)
def ginger_form_attrs(form,**kwargs):
    return get_form_attrs(form,**kwargs)


@ginger_tag(mark_safe=True)
def ginger_form_submit(form,  **kwargs):
    return create_submit_tag(form, **kwargs)


@ginger_tag()
def ginger_form_submit_name(form):
    return gutils.get_form_submit_name(form)

@ginger_tag(takes_context=True, mark_safe=True)
def ginger_form_begin(context,form,**kwargs):
    kwargs = kwargs.copy() 
    content = [create_form_tag(form,**kwargs),create_csrf_tag(context)]
    return " ".join(content)


@ginger_tag(mark_safe=True)
def ginger_form_end(form,submit=None,**kwargs):    
    tag = "</form>"
    content = [tag]
    if submit:
        name = gutils.get_form_submit_name(form)
        content.append(create_submit_tag(form,submit,name))
    return " ".join(content)


@ginger_tag(takes_context=True, mark_safe=True)
def ginger_form(context,form,**kwargs):
    layout = kwargs.pop('layout',None)     
    csrf = create_csrf_tag(context)
    name = gutils.get_form_submit_name(form)
    value = "Submit"
    submit = create_submit_tag(form,name=name,value=value,**kwargs)
    fields = map(lambda f: render_field(f, {'layout': layout}),(form[key] for key in form.fields) )
    fields.append(submit)
    fields.insert(0,csrf)
    fields.insert(0,create_form_tag(form))
    fields.append("</form>")
    return "".join( fields )


@ginger_tag()
def ginger_form_slice(first=None,last=None,form=None,**kwargs):
    if hasattr(first, 'fields'):
        form = first
        first = None
    else:
        form = getattr(first,'form', getattr(last,'form',form)) 
    keys = form.fields.keys()
    first = keys.index( first.name ) if first else None
    last = keys.index( last.name ) + 1  if last else None
    return ginger_fields( *list(form[field] for field in  keys[first:last]), **kwargs)

        
@ginger_tag(mark_safe=True)        
def ginger_fields(*fields,**kwargs):
    content = map(lambda f : render_field(f, kwargs), fields)    
    return "".join(content)

            
@ginger_tag(mark_safe=True)            
def ginger_field(field, **kwargs):      
    return render_field(field, kwargs)

def get_css_prefix():
    return getattr(settings,"GINGER_CSS_PREFIX", "gui-")

def format_errors(error_list, **kwargs):
    if not error_list:
        return "<ul class='errorlist'></ul>"
    return str(error_list)

def render_field(field, kwargs):
    if field.is_hidden:
        return str(field) 
    layout = kwargs.pop("layout", None) or "default"     
    inject_validation_tags(field)  
    process = lambda a: gutils.camel_to_hyphen(re.sub( r'widget|field', '',a.__class__.__name__)).lower()
    attrs = kwargs
    attrs =  make_attrs(attrs)    
    field_class_name = process(field.field)        
    widget = field.field.widget
    widget_class_name = process(widget)  
    template_name = "fields/%s.html"%field_class_name.replace("-", "_")
    field_name = field.name
    is_valid = not field.errors
    context = {
               'is_valid': is_valid,
               'field_errors': format_errors(field.errors),
               'prefix': get_css_prefix(),
               'field': field,
               'field_name': field_name,
               'field_class': field_class_name,
               'widget': widget,
               'widget_class': widget_class_name,
               'attributes': attrs
    }    
    template = [template_name, "ginger/fields/%s.html"%layout]
    html = render_to_string(template, context)
    return html    


def inject_validation_tags(bound_field):
    field = bound_field.field    
    widget = field.widget    
        
    attrs = {
             'max_length':'maxlength',
             'min_length':'minlength',
#             'regex':'pattern',
#             'required':'required'
    }          
    
    convert = {
               '*': lambda a : json.dumps(a), 
#               'regex': lambda a: str(a.pattern).encode('string-escape') 
    }
    
    if field.required: widget.attrs['required'] = 1
    
    for k,v in attrs.iteritems():
        val = getattr(field, k, None)
        if val is not None:                      
            widget.attrs[v] = convert.get(k, convert['*'])(val)
    

@ginger_tag(mark_safe=True)
def ginger_widget(field,**kwargs):
    wid = field.field.widget
    wid.attrs.update(kwargs)
    return unicode(field)
    