import os.path
import datetime
from django.conf import settings
from django.template import defaultfilters as filters
from django.template.defaulttags import CsrfTokenNode
from django.forms.forms import pretty_name
from django.db import models
from django.utils import dateformat
from django.utils.html import escape
from django.utils.encoding import force_unicode
from django.utils.safestring import SafeData, EscapeData, mark_safe
from django.contrib.humanize.templatetags import humanize

#relative import to get original template display attribute
from ..template import templatetags as dhtags

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

def display_attribute(context, obj, attribute, max_length=None, if_trunc="...", if_none="No %(attribute)s", if_date=None):
    return dhtags.display_attribute(context, obj, attribute, max_length, if_trunc, if_none, if_date)

#http://www.davidcramer.net/code/429/scaling-your-frontend-far-futures-headers-and-template-tags.html
def mediaurl(context, value, base_url=None):
    return dhtags.mediaurl(context, value, base_url=None)

def css_tags(context, media_url='/public'):
    return dhtags.css_tags(context, media_url=media_url)

def js_tags(context, media_url='/public'):
    return dhtags.js_tags(context, media_url=media_url)
