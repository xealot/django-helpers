from django.conf import settings

def common(request):
    c = {'MEDIA_URL': settings.MEDIA_URL,
         'DEBUG': settings.DEBUG,
         'USE_DEPLOY_FILES': settings.USE_DEPLOY_FILES, 
         'UA_NOTICE': None,
         'REFERRER': request.META.get('HTTP_REFERER') if 'HTTP_REFERER' in request.META else ''}
    if request.is_secure():
        c['MEDIA_URL'] = settings.MEDIA_URL_SSL
    return c