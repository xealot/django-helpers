"""
Middleware to redirect to an SSL version of a page when 
it requires SSL in the urlconf and to pull out of SSL
when it's not required.

(r'^acount/', include('urls'), {SSL: True}),

This requires a setting of ENABLE_SSL to work
ENABLE_SSL = True #SSL enabled
ENABLE_SSL = False #SSL disabled

#SSL_FORCE_RETURN
#If force return is true, this means that if SSL is not specified 
#the page will always redirect back to a regular non-ssl version.

"""
from django.conf import settings
from django.http import HttpResponseRedirect, get_host
from django.core.exceptions import MiddlewareNotUsed

SSL = 'SSL'
#SSL_FORCE_RETURN = True

class SSLRedirectMiddleware(object):
    def __init__(self):
        if getattr(settings, 'DEBUG', False) is True or getattr(settings, 'ENABLE_SSL', False) is False:
            raise MiddlewareNotUsed

    def process_view(self, request, view_func, view_args, view_kwargs):
        secure = view_kwargs.pop(SSL, None)
        if secure is None: #If SSL is None, do NOT redirect
            return None

        if secure != request.is_secure():
            if request.method == 'POST':
                raise RuntimeError, \
                """Can't perform a SSL redirect while maintaining POST data.
                   Please structure your views so that redirects only occur during GETs."""
            return self._redirect(request, secure)

    def _redirect(self, request, secure):
        protocol = 'https' if secure is True else 'http'
        newurl = "%s://%s%s" % (protocol, get_host(request), request.get_full_path())
        return HttpResponseRedirect(newurl)

# If request.is_secure isn't right for you
#    def _is_secure(self, request):
#        if request.is_secure():
#            return True
#
#        if 'HTTP_X_FORWARDED_SSL' in request.META:
#            return request.META['HTTP_X_FORWARDED_SSL'] == 'on'
#
#        return False

    