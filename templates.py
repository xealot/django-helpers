import datetime
from decimal import Decimal

from django.db import models
from django.utils.html import escape

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

