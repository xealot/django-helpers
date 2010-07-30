import sys
from django.conf import settings
from django.http import HttpResponse
from django.template.context import Context, RequestContext
from django.template import loader
from django.core.exceptions import MiddlewareNotUsed
from functools import wraps

#:TODO: I probably only need one of these, unify implementation to only use DEBUG_FLAG
DEBUG_FLAG = '_do_debug'
URL_DEBUG_FLAG = 'debug'

def no_debug(func):
    """
    Decorator for views that will disable debugging output for the 
    decorated view.
    """
    @wraps(func)
    def wrapper(request, *args, **kwds):
        setattr(request, DEBUG_FLAG, False)
        return func(request, *args, **kwds)
    return wrapper


class DebugMiddleware(object):
    def __init__(self):
        if settings.DEBUG is False:
            raise MiddlewareNotUsed

    def process_request(self, request):
        """ Check IP's and request to see if we should debug. """
        setattr(request, DEBUG_FLAG, settings.DEBUG)
        if not settings.INTERNAL_IPS or request.META.get('REMOTE_ADDR', '') in settings.INTERNAL_IPS:
            setattr(request, DEBUG_FLAG, True)
        if request.is_ajax():
            setattr(request, DEBUG_FLAG, False)
        if URL_DEBUG_FLAG in request.GET:
            setattr(request, DEBUG_FLAG, True)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'debug' in view_kwargs:
            setattr(request, DEBUG_FLAG, bool(view_kwargs.pop('debug')))
        return None

    def should_debug(self, request, response):
        if not hasattr(request, DEBUG_FLAG):
            #This happens when the request is thrown away and a new one used instead. Common on middleware exceptions
            setattr(request, DEBUG_FLAG, settings.DEBUG)
        if getattr(request, DEBUG_FLAG) is False:
            return False
        if getattr(response, DEBUG_FLAG, True) is False:
            return False

        # Only attach debugging to valid HTTP responses.
        # HTTPResponse can be a subclass of itself, but HttpResponse 
        # won't be a child of HttpResponse*
        if isinstance(response, HttpResponse) and issubclass(HttpResponse, response.__class__):
                # Make sure the content-type is the right type.
                if response.has_header('content-type') and response._headers['content-type'][1].startswith('text/html'):
                    return True
        return False
    
    def process_response(self, request, response):
        # We import this here so connection is only created during debug
        if self.should_debug(request, response):
            from django.db import connection
            try:
                # This force_unicode() around response.content is necessary if the page
                # rendered includes some crazy Unicode stuff.  Don't know why casting
                # loader.render_to_string as unicode wouldn't fix it, but it didn't.
                context = Context({
                    'request': request,
                    'debug': True,
                    'sql_queries': connection.queries,
                    #'cache_profile': cache.cache.profile
                })
                response.write(loader.render_to_string('/custom_debug.html', context_instance=context))
            except:
                try:
                    response.write('Could not render debug.  Stack trace: %s' % str(sys.exc_info()))
                except:
                    pass
        return response


class DebugStripMiddleware(object):
    """
    This class comes after the DebugMiddleware class 
    to make sure that debug keys get stripped from the 
    view kwargs.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        view_kwargs.pop('debug', None)
        return None


