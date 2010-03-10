import os.path
from django.template.defaulttags import CsrfTokenNode
import datetime

from django.conf import settings
from django.template import defaultfilters as filters
from django.forms.forms import pretty_name
from django.db import models
from django.utils import dateformat
from django.utils.html import escape
from django.utils.encoding import force_unicode
from django.utils.safestring import SafeData, EscapeData, mark_safe
from django.contrib.humanize.templatetags import humanize

from helpers import templates as general_templates

def safe(obj):
    text = force_unicode(obj)
    if (not isinstance(text, SafeData)) or isinstance(text, EscapeData):
        return escape(text)
    return text

def date(context, value, arg=None):
    if value == 'now':
        value = datetime.datetime.now()
    return filters.date(value, arg)

def pluralize(context, value, arg=None):
    return filters.pluralize(value, arg)

def yesno(context, value, arg=None):
    return filters.yesno(value, arg)

def wordwrap(context, value, arg=None):
    return filters.wordwrap(value, arg)

def timesince(context, value, arg=None):
    return filters.timesince(value, arg)

def timeuntil(context, value, arg=None):
    return filters.timeuntil(value, arg)

def unordered_list(context, value):
    return filters.unordered_list(value)

def ordinal(context, value):
    return humanize.ordinal(value)

#Is there a way to pass context implicitly? Probably Not...
def url(context, view_name, args=None, kwargs=None):
    from django.core.urlresolvers import reverse, NoReverseMatch
    try:
        #request = context.get('request', None)
        urlconf = hasattr(context['request'], 'urlconf') and context['request'].urlconf or None 
        return reverse(view_name, urlconf=urlconf, current_app=context.get('current_app', None), args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ''

def csrf_token(context):
    return CsrfTokenNode().render(context)

def is_multipart(context, form):
    if form.is_multipart:
        return 'enctype="multipart/form-data"'
    
def allowed(context, key):
    return context['request'].user.has_perm(key)

#http://www.davidcramer.net/code/429/scaling-your-frontend-far-futures-headers-and-template-tags.html
def mediaurl(context, value, base_url=None):
    base_url = base_url if base_url is not None else settings.MEDIA_URL
    fname = os.path.abspath(os.path.join(settings.MEDIA_ROOT, value))
    if not fname.startswith(settings.MEDIA_ROOT):
        raise ValueError("Media must be located within MEDIA_ROOT.")
    return '%s%s?%s' % (base_url, value, unicode(int(os.stat(fname).st_mtime)))

def display_attribute(context, obj, attribute, max_length=None, if_trunc="...", if_none="No %(attribute)s", if_date=None):
    return general_templates(obj, attribute, max_length, if_trunc, if_none, if_date)

def css_tags(context, media_url='/public'):
    if hasattr(settings, 'DEPLOY_CSS'):
        output = []
        for t in settings.DEPLOY_CSS:
            output.append('<link rel="stylesheet" href="%s/css/%s" type="text/css" media="screen" />' % (media_url, t))
        return '\n'.join(output)
    return ''

def js_tags(context, media_url='/public'):
    if hasattr(settings, 'DEPLOY_JS'):
        output = []
        for t in settings.DEPLOY_JS:
            output.append('<script src="%s/js/%s" type="text/javascript"></script>' % (media_url, t))
        return '\n'.join(output)
    return ''
