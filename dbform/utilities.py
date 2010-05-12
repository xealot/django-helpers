from django.utils.datastructures import SortedDict
from django import forms
from django.db import models
from cgi import parse_qs
from django.utils import simplejson as json
from django.template import Context, Template
from forms import DBForm

TYPE_TEXT = 1
TYPE_CHOICE = 2
TYPE_DB_ENTITY = 3
TYPE_LARGE_TEXT = 4
TYPE_BOOL = 5
TYPE_IMAGE = 6

COERCE_BOOLEAN_VALUES = ('no', 'false', '0', '')

def dbform_factory(formdef, querysets=None):
    """Take a FormDef instance and create a real django form out of it"""
    base_fields = SortedDict()
    key_to_field_id = {} #This is so the save function on DBForm has enough information to save
    for field in formdef.field_set.select_related():
        key_to_field_id[field.key] = field
        default_args = {'required': field.required, 'help_text': field.help_text, 'label': field.label, 'initial': field.default}
        if field.type.pk == TYPE_TEXT:
            base_fields[field.key] = forms.CharField(max_length=100, **default_args)
        if field.type.pk == TYPE_CHOICE:
            choices = [(v,v) for v in field.field_data.split('|')]
            base_fields[field.key] = forms.ChoiceField(choices=choices, widget=forms.RadioSelect, **default_args)
        if field.type.pk == TYPE_DB_ENTITY:
            if querysets is not None and field.key in querysets:
                qs = querysets[field.key]
            else:
                app_label, model_name = field.field_data.split('.')
                Model = models.get_model(app_label, model_name)
                qs = Model.objects.all()
            base_fields[field.key] = forms.ModelChoiceField(qs, **default_args)
        if field.type.pk == TYPE_BOOL:
            base_fields[field.key] = forms.BooleanField(widget=forms.RadioSelect(choices=((True, 'Yes'),(False, 'No'))), **default_args)
        if field.type.pk == TYPE_IMAGE:
            base_fields[field.key] = forms.ImageField(**default_args)

        #Apply HTML attributes to widget.attrs
        final_attrs = {}
        if field.html_attr:
            attrs = parse_qs(field.html_attr, keep_blank_values=True)
            #I'm making the assumption here that since these are HTML attributes that lists should be combined with ' '
            for k,v in attrs.items():
                final_attrs[k] = ' '.join(v)

        #USE WITH jquery.metadata -- Apply non-field data as css attribute as well; this is separate because they service separate purposes.
        if field.nonfield_data:
            value = json.dumps(field.nonfield_data).replace('"', "'")
            if 'class' in final_attrs:
                final_attrs['class'] += ' %s' % value
            else:
                final_attrs['class'] = value
        base_fields[field.key].widget.attrs.update(final_attrs)
#        if var.type.name == "Large Text":
#            fields[key] = forms.CharField(widget=forms.Textarea, **default_args)
#        if var.type.name == "Reference":
#            fields[key] = forms.CharField(max_length=100, **default_args)
    #inheritance = tuple([DBVarForm])
    DBFormClass = type(str('%sDBForm' % formdef.name), (DBForm,), {'base_fields':base_fields, 'key_to_field_id': key_to_field_id})
    return DBFormClass

#:TODO: this might be a little dangerous, when an RE and resolve function will do.
def resolve_default(context, text):
    return Template(text).render(Context(context))

def coerce_field(field, value):
    if field.type.pk == TYPE_BOOL:
        if value.lower() in COERCE_BOOLEAN_VALUES:
            return False
        else:
            return True
    
    return value

def dbform_values(SavedModel, formdef, context=None, narrow=None):
    """
    Return a Sorted Dictionary of {Field: Resolved Value}, this 
    is useful for displaying what is saved in the dbform.
    """
    narrow = narrow or {}
    field_vals = SortedDict()
    #Setup default dictionary
    all_fields = formdef.field_set.select_related()
    for f in all_fields:
        field_vals[f] = f.default
    #Apply any saved user data
    saved_data = SavedModel.objects.select_related().filter(field__form=formdef, **narrow)
    for d in saved_data:
        field_vals[d.field] = d.value
    #Resolve and Coerce fields
    for f, v in field_vals.items():
        field_vals[f] = coerce_field(f, resolve_default(context, v))
    return field_vals

def dbform_context(SavedModel, formdef, context=None, narrow=None):
    """
    This function returns a Sorted Dictionary of {key: value} for use 
    with templates and variable substitution.
    """
    data = dbform_values(SavedModel, formdef, context=context, narrow=narrow)
    values = SortedDict()
    for f, v in data.items():
        values[f.key] = v
    return values






