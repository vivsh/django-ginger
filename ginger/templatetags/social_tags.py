from ginger.template import Library as GingerLibrary
from allauth.socialaccount import providers


ginger = GingerLibrary()


@ginger.tag(takes_context=True)
def provider_login_url(context, provider_id, **query):
    provider = providers.registry.by_id(provider_id)
    request = context['request']
    if 'next' not in query:
        next = request.REQUEST.get('next')
        if next:
            query['next'] = next
    else:
        if not query['next']:
            del query['next']
    return provider.get_login_url(request, **query) 


@ginger.tag(takes_context=True)
def provider_media_js(context):
    request = context['request']
    ret = '\n'.join([p.media_js(request) 
                     for p in providers.registry.get_list()])
    return ret    
