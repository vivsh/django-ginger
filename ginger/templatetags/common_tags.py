from ginger import template
from ginger.utils import update_request_query, get_form_submit_name
from datetime import datetime


LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
NUM_PAGES_OUTSIDE_RANGE = 2 
ADJACENT_PAGES = 4

registry = template.Library()

@registry.tag(takes_context=True)
def current_url(context,*args,**kwargs):    
    request = context['request']
    return update_request_query(request,*args,**kwargs)


@registry.tag(template="commons/tags/pagination.jinja",takes_context=True)
def paginate(context,page_obj):    
    request = context.get('request')   
    
    is_paginated = True   
        
    in_leading_range = in_trailing_range = False
    pages_outside_leading_range = pages_outside_trailing_range = range(0)        
    num_pages = page_obj.paginator.num_pages
    current_page = page_obj.number
    base_url = request.path_info
    if ( num_pages <= LEADING_PAGE_RANGE_DISPLAYED):
        in_leading_range = in_trailing_range = True
        page_numbers = [n for n in range(1, num_pages + 1) if n > 0 and n <= num_pages]           
    elif (current_page <= LEADING_PAGE_RANGE):
        in_leading_range = True
        page_numbers = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1) if n > 0 and n <= num_pages]
        pages_outside_leading_range = [n + num_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
    elif (current_page > num_pages - TRAILING_PAGE_RANGE):
        in_trailing_range = True
        page_numbers = [n for n in range(num_pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, num_pages + 1) if n > 0 and n <= num_pages]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    else: 
        page_numbers = [n for n in range(current_page - ADJACENT_PAGES, current_page + ADJACENT_PAGES + 1) if n > 0 and n <= num_pages]
        pages_outside_leading_range = [n + num_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    return {
        "page_field_name":getattr(page_obj,'page_field_name','page'),
        "page_url": base_url,
        'page_obj':page_obj,
        'paginator':page_obj.paginator,
        "is_paginated": is_paginated,            
        "page": current_page,
        "pages": num_pages,
        "page_numbers": page_numbers,
        "in_leading_range" : in_leading_range,
        "in_trailing_range" : in_trailing_range,
        "pages_outside_leading_range": pages_outside_leading_range,
        "pages_outside_trailing_range": pages_outside_trailing_range
    }
    

@registry.filter
def local_datetime(stamp, large=True):
    #April 3rd 2013, 10:50am
    suffix = {
      '1': 'st',
      '3': 'rd'
    }
    month = str(stamp.month)[-1]
    suffix = suffix.get(month, 'th')
    fmt = "%B %d{suffix} %Y, %I:%M %p".format(suffix=suffix)
    if not large:
        fmt = "%B %d{suffix} %I:%M %p".format(suffix=suffix)
    return stamp.strftime(fmt)

