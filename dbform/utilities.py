from django.utils.datastructures import SortedDict
from django import forms
from django.db import models
from cgi import parse_qs
from django.utils import simplejson as json
from django.template import Context, Template

COERCE_BOOLEAN_VALUES = ('no', 'false', '0', '')

#:TODO: this might be a little dangerous, when an RE and resolve function will do.
def resolve_default(context, text):
    if isinstance(text, basestring):
        return Template(text).render(Context(context))
    return text

def coerce_field(field, value):
    from forms import TYPE_BOOL
    if field.type_id == TYPE_BOOL:
        if value.lower() in COERCE_BOOLEAN_VALUES:
            return False
        else:
            return True
    return value

def dbform_resolve(field_value_dict, context):
    for f, v in field_value_dict.items():
        field_value_dict[f] = coerce_field(f, resolve_default(context, v))
    return field_value_dict

#:TODO: this is cacheable.
def dbform_defaults(formdef, context=None, resolve=True):
    """
    Get default values from form definition based on template 
    rendering and context.
    """
    assert context is not None or resolve is False, 'If you specify resolve=True you must supply a context'
    all_fields = formdef.field_set.select_related()
    defaults = SortedDict()
    for f in all_fields:
        defaults[f] = resolve_default(context, f.default) if resolve is True else f.default
    return defaults

def dbform_values(SavedModel, formdef, context=None, narrow=None):
    """
    Return a Sorted Dictionary of {Field: Resolved Value}, this 
    is useful for displaying what is saved in the dbform.
    """
    values = dbform_defaults(formdef, context, resolve=False)
    #Apply any saved user data !This cannot be the same query as the default getter, since unsaved fields would not return a row!
    values.update(dict([(r.field, r.value) for r in SavedModel.objects.select_related('field__type').filter(field__form=formdef, **narrow or {}).defer('blob')]))
    #Resolve and Coerce fields
    return dbform_resolve(values, context)

def dbform_context(SavedModel, formdef, context=None, narrow=None):
    """
    This function returns a Sorted Dictionary of {key: value} for use 
    with templates and variable substitution.
    """
    data = dbform_values(SavedModel, formdef, context=context, narrow=narrow)
    values = SortedDict()
    for f, v in data.items():
        #if f.type_id == 6:
            #v = {'filename': v, 'bin': }
        values[f.key] = v
    return values






