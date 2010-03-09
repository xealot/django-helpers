from django.conf import settings

def vars(request):
    c = {'CORP_NAME': settings.CORP_NAME,
         'CORP_DOMAIN': settings.CORP_DOMAIN,
         'CORP_URL': settings.CORP_URL,
         'MEDIA_URL': settings.MEDIA_URL,
         'DEBUG': settings.DEBUG}

    if request.is_secure():
        c['MEDIA_URL'] = settings.MEDIA_URL_SSL

    c['REFERER'] = 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'] or None

    return c
