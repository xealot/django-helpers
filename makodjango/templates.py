import os.path
from django.template.defaulttags import CsrfTokenNode
import datetime
from django.db.models.fields import FieldDoesNotExist
from decimal import Decimal

from django.conf import settings
from django.template import defaultfilters as filters
from django.forms.forms import pretty_name
from django.db import models
from django.utils import dateformat
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.encoding import force_unicode
from django.utils.safestring import SafeData, EscapeData, mark_safe
from django.utils.translation import get_date_formats
from django.contrib.humanize.templatetags import humanize

EMPTY_CHANGELIST_VALUE = '(None)'

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

#:TODO: REFACTOR THIS, from 66:105 was clipped in from django admin.
def display_attribute(context, obj, attribute, max_length=None, if_trunc="...", if_none="No %(attribute)s", if_date=None):
    format_kw = {'max_length': max_length, 'truncate': if_trunc, 'null': if_none, 'empty': if_none, 'attribute': attribute}
 
    #output = unicode(value)
    if isinstance(obj, models.Model):
        #We can infer a few special cases if the object is a Model instance.
        try:
            f = obj.__class__._meta.get_field(attribute)
        except FieldDoesNotExist:
            value = getattr(obj, attribute, None)
            if callable(value):
                value = value()
        else:
            if isinstance(f.rel, models.ManyToOneRel):
                value = getattr(obj, f.name)
            else:
                value = getattr(obj, f.get_attname(), None)
                if isinstance(f, models.BooleanField) or isinstance(f, models.NullBooleanField):
                    format_kw['cast'], format_kw['max_length'] = bool, None
                elif f.flatchoices:
                    format_kw['map'] = dict(f.flatchoices)
    elif isinstance(obj, dict):
        value = obj.get(attribute, None)
    else:
        value = getattr(obj, attribute, None) or None

    return general_formatter(value, **format_kw)

def general_formatter(value, cast=None, **kwargs):
    """
    Intelligently format typed data
    """
    if cast is not None:
        value = cast(value)
    if isinstance(value, (datetime.datetime, datetime.time, datetime.date)):
        if value:
            date_format, datetime_format, time_format = get_date_formats()
            if isinstance(value, datetime.datetime):
                result_repr = capfirst(dateformat.format(value, datetime_format))
            elif isinstance(value, datetime.time):
                result_repr = capfirst(dateformat.time_format(value, time_format))
            else:
                result_repr = capfirst(dateformat.format(value, date_format))
        else:
            result_repr = EMPTY_CHANGELIST_VALUE
    elif isinstance(value, models.Model):
        result_repr = unicode(value)
    elif isinstance(value, bool):
        result_repr = _boolean_icon(value)
    elif isinstance(object, (float, Decimal)):
        if value is not None:
            result_repr = ('%%.%sf' % kwargs.get('places', 2)) % value
        else:
            result_repr = EMPTY_CHANGELIST_VALUE
    elif 'map' in kwargs:
        result_repr = kwargs['map'].get(value, EMPTY_CHANGELIST_VALUE)
    else:
        result_repr = value
    
    if 'null' in kwargs and result_repr is None:
        result_repr = kwargs.get('null', EMPTY_CHANGELIST_VALUE)  % {'attribute': kwargs.get('attribute', '')}
    if 'empty' in kwargs and result_repr == '':
        #pretty_name(if_none % {'attribute': attribute})
        result_repr = kwargs.get('empty', EMPTY_CHANGELIST_VALUE) % {'attribute': kwargs.get('attribute', '')} 
    if kwargs.get('max_length', False):
        result_repr = escape(result_repr) #This turns INT into UNICODE, necessary for max_len
        if len(result_repr) > kwargs['max_length']:
            result_repr = mark_safe(u'<abbr title="%s">%s</abbr>' % (result_repr, 
                                                          result_repr[:kwargs['max_length']-len(kwargs.get('truncate', ''))] + kwargs.get('truncate', '')))
    return result_repr

def _boolean_icon(field_val):
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    return mark_safe(u'<img src="%simg/admin/icon-%s.gif" alt="%s" />' % (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], field_val))

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

#CRUMB_ROOT = 'crumb_root'
#CRUMB_LIST = 'crumb_list'
#def add_crumb(context, name, view_name, root=False, args=None, kwargs=None):
#    obj = {'name':name, 'view_name': view_name, 'args': args, 'kwargs': kwargs}
#    if not root:
#        #Add to session, do not duplicate
#        session = context['request'].session
#        if CRUMB_LIST not in session:
#            session[CRUMB_LIST] = []
#        if len(session[CRUMB_LIST]) > 50:
#            session[CRUMB_LIST] = session[CRUMB_LIST][-50:]
#        #if obj not in session:
#        session[CRUMB_LIST].append(obj)
#    else:
#        if CRUMB_ROOT not in context['attributes']:
#            context['attributes'][CRUMB_ROOT] = []
#        context['attributes'][CRUMB_ROOT].append(obj)
#    return ''
#
#def show_crumbs(context):
#    atts = context['attributes']
#    session = context['request'].session
#    output = ''
#    print atts
#    if CRUMB_ROOT in atts and atts[CRUMB_ROOT]:
#        roots = []
#        for crumb in atts[CRUMB_ROOT]:
#            roots.append("<a href="+url(context, crumb['view_name'], crumb['args'], crumb['kwargs'])+">"+crumb['name']+"</a>")
#        output += ' ++ '.join(roots)
#    if CRUMB_LIST in session and session[CRUMB_LIST]:
#        crumbs = []
#        for crumb in session[CRUMB_LIST][-5:]:
#            crumbs.append("<a href="+url(context, crumb['view_name'], crumb['args'], crumb['kwargs'])+">"+crumb['name']+"</a>")
#        output += ' -- '.join(crumbs)
#    return output






