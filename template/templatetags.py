import datetime
from decimal import Decimal

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.html import escape
from django.utils.safestring import mark_safe, SafeUnicode, SafeString
from django.utils.text import capfirst
from django.utils import dateformat
from django.conf import settings
import os

EMPTY_CHANGELIST_VALUE = '(None)'

#:TODO: REFACTOR THIS, from 66:105 was clipped in from django admin.
def display_attribute(obj, attribute, max_length=None, if_trunc="...", if_none="No %(attribute)s", if_date=None):
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

#:TODO: give this a real signature instead of just kwargs, jesus
def general_formatter(value, cast=None, **kwargs):
    """
    Intelligently format typed data
    """
    if value is None:
        if 'null' in kwargs:
            value = kwargs.get('null', EMPTY_CHANGELIST_VALUE)  % {'attribute': kwargs.get('attribute', '')}
        else:
            value = EMPTY_CHANGELIST_VALUE
    if cast is not None:
        value = cast(value)

    if isinstance(value, (datetime.datetime, datetime.time, datetime.date)):
        if isinstance(value, datetime.datetime):
            result_repr = capfirst(dateformat.format(value, settings.DATE_FORMAT))
        elif isinstance(value, datetime.time):
            result_repr = capfirst(dateformat.time_format(value, settings.TIME_FORMAT))
        else:
            result_repr = capfirst(dateformat.format(value, settings.DATE_FORMAT))
    elif isinstance(value, bool):
        result_repr = _boolean_icon(value)
    elif isinstance(value, (float, Decimal)):
        result_repr = (u'%%.%sf' % kwargs.get('places', 2)) % value
    elif 'map' in kwargs:
        result_repr = kwargs['map'].get(value, EMPTY_CHANGELIST_VALUE)
    elif isinstance(value, (SafeUnicode, SafeString)):
        result_repr = value
    else:
        result_repr = unicode(value)
    
    if 'empty' in kwargs and result_repr == '':
        result_repr = kwargs.get('empty', EMPTY_CHANGELIST_VALUE) % {'attribute': kwargs.get('attribute', '')} 
    
    if not isinstance(result_repr, (SafeUnicode, SafeString)) and kwargs.get('max_length', False) and len(result_repr) > kwargs['max_length']:
        result_repr = mark_safe(u'<abbr title="%s">%s</abbr>' % (result_repr, 
                                                       result_repr[:kwargs['max_length']-len(kwargs.get('truncate', ''))] + kwargs.get('truncate', '')))
    return result_repr

#:TODO: make this image a settings entry, default to the admin version
def _boolean_icon(field_val):
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    return mark_safe(u'<img src="%simg/admin/icon-%s.gif" alt="%s" />' % (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], field_val))

#http://www.davidcramer.net/code/429/scaling-your-frontend-far-futures-headers-and-template-tags.html
def mediaurl(value, base_url=None):
    base_url = base_url if base_url is not None else settings.MEDIA_URL
    fname = os.path.abspath(os.path.join(settings.MEDIA_ROOT, value))
    if not fname.startswith(settings.MEDIA_ROOT):
        raise ValueError("Media must be located within MEDIA_ROOT.")
    return '%s%s?%s' % (base_url, value, unicode(int(os.stat(fname).st_mtime)))

def css_tags(media_url='/public'):
    if hasattr(settings, 'CSS_FILES'):
        output = []
        for t in settings.CSS_FILES:
            output.append('<link rel="stylesheet" href="%s/%s" type="text/css" media="screen" />' % (media_url, t))
        return '\n'.join(output)
    return ''

def js_tags(media_url='/public'):
    if hasattr(settings, 'JS_FILES'):
        output = []
        for t in settings.JS_FILES:
            output.append('<script src="%s/%s" type="text/javascript"></script>' % (media_url, t))
        return '\n'.join(output)
    return ''
