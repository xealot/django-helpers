from urllib import urlencode
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import _get_queryset, render_to_response as rtr
from django.template.context import RequestContext
from decorator import decorator
from functools import partial
import re
from middleware.debug import DEBUG_FLAG
from django.template import loader

PARAM_PREFIX = 'f_' #I consider this an improvement over the django version

#This one liner is to alleviate the need to but a form definition in a branching IF
post_data = lambda request: request.POST if request.method == 'POST' else None
pd = lambda request: request.POST if request.method == 'POST' else None
pf = lambda request: request.FILES if request.method == 'POST' else None
#Python 2.6 only... BAH
pfd = lambda request: (request.POST, request.FILES) if request.method == 'POST' else (None, None) 

def decorator_factory(decfac): # partial is functools.partial
    "decorator_factory(decfac) returns a one-parameter family of decorators"
    return partial(lambda df, param: decorator(partial(df, param)), decfac)

@decorator_factory
def render_to(template, func, request, *args, **kw):
    """
    A decorator for view functions which will accept a template parameter 
    and then execute render_to_response. Views should return a context.
    
    @render_to('template')
    def view_func(request):
        return {'form': form}
    """
    output = func(request, *args, **kw)
    if isinstance(output, (list, tuple)):
        return render_to_response(request, output[1], output[0])
    elif isinstance(output, dict):
        return render_to_response(request, template, output)
    return output

def redirect(*args, **kwargs):
    """Creates a redirect response and accepts the same parameters as reverse.
    The reverse functionality can be overridden by passing in a named attributes 'url'
    keyword qs takes a dict and will create a query string"""
    if 'url' in kwargs:
        return HttpResponseRedirect(kwargs['url'])
    
    qs = ''
    if 'qs' in kwargs:
        qs = '?'+urlencode(kwargs.pop('qs'), True)
    
    return HttpResponseRedirect(reverse(*args, **kwargs)+qs)

def redirect_to_referrer(request, fallback=None, *args, **kwargs):
    """Creates an HttpResponse back to the referrer, if no referrer was specified 
    then it uses the fallback kwarg."""
    if 'HTTP_REFERER' in request.META:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if fallback:
        return redirect(fallback)
    return HttpResponseRedirect("/")

def get_object_or_none(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None

def direct_to_template(request, template, extra_context=None, mimetype=None, **kwargs):
    """
    Render a given template with any extra URL parameters in the context as
    ``{{ params }}``.
    """
    if extra_context is None: extra_context = {}
    dictionary = {'params': kwargs}
    for key, value in extra_context.items():
        if callable(value):
            dictionary[key] = value()
        else:
            dictionary[key] = value
    return render_to_response(request, template, dictionary, mimetype=mimetype)

#:TODO: these _to_ function might be able to consolidate.
def render_to_string(request, template, dictionary=None):
    return loader.render_to_string(template, dictionary, context_instance=RequestContext(request))

def render_to_response(request, template, dictionary=None, no_debug=False, cookies=None, **kwargs):
    """
    REQUIRES Request as first argument.
    
    A more advanced version of render_to_response that is 
    able to handle the debug flag as well as set cookies. 
    
    The main improvement with this render_to_response is the automatic 
    inclusion of RequestContext(), as I've never seen and instance where 
    this would not be desirable to have.
    """
    response = rtr(template, dictionary, context_instance=RequestContext(request), **kwargs)

    if cookies:
        for cookie in cookies:
            response.set_cookie(**cookie)
    
    if no_debug is True:
        setattr(response, DEBUG_FLAG, False)
    return response

def direct_to_response(request, content, no_debug=False, cookies=None, **kwargs):
    response = HttpResponse(content, **kwargs)

    if cookies:
        for cookie in cookies:
            response.set_cookie(**cookie)
    
    if no_debug is True:
        setattr(response, DEBUG_FLAG, False)
    return response

def split_param_prefixes(params, prefix=PARAM_PREFIX):
    prefixed, other = [], []
    for i, v in params.items():
        if prefix is not None and i[:len(prefix)] == prefix:
            prefixed.append((str(i[len(prefix):]), v))
        else:
            other.append((str(i), v))
    return dict(prefixed), dict(other)

def get_query_string(params, new_params=None, remove=None, prefix=None):
    """
    Prefix will cause this function to both only produce query string variables 
    containing a certain prefix and to only read or modify params with a particular 
    prefix.
    """
    if new_params is None: new_params = {}
    if remove is None: remove = []
    p, p_all = split_param_prefixes(params, prefix)
    for r in remove:
        for k in p.keys():
            if k.startswith(r):
                del p[k]
    for k, v in new_params.items():
        if v is None:
            if k in p:
                del p[k]
        else:
            p[k] = v
    if prefix is not None:
        p = dict([(prefix+i, v) for i, v in p.items()])
    p_all.update(p)
    return '?%s' % urlencode(p_all)

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to underscores.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '_', value)

def random_password(minpairs=3, maxpairs=4):
    '''Create a random password as pairs of consonants and vowels.  The 
    number of "pairs" is chosen randomly between minpairs and maxpairs.  
    The letters are also randomly capitalized (50/50 chance)'''
    import random, string
    
    vowels='aeiou'
    consonants='bcdfghjklmnpqrstvwxyz'
    password=''

    for x in range(1,random.randint(int(minpairs),int(maxpairs))):
        consonant = consonants[random.randint(1,len(consonants)-1)]
        if random.choice([1,0]):
            consonant = string.upper(consonant)
        password = password + consonant
        vowel = vowels[random.randint(1,len(vowels)-1)]
        if random.choice([1,0]):
            vowel = string.upper(vowel)
        password = password + vowel
    return password