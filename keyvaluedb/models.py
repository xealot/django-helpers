from django.core.exceptions import MultipleObjectsReturned
from django.db.models.base import Model
from django.db import models
from ..fields.binary import BlobField
from django.forms import fields

COERCE_FALSE_VALS = ('0', '', 'False', 'false')

class SavedValue(models.Model):
    key = models.SlugField(max_length=100, editable=False)
    value = models.TextField(null=True, blank=True)
    blob = BlobField(null=True, blank=True)
    coerce = models.CharField(max_length=10, null=True, blank=True)
    
    @property
    def final(self):
        if self.coerce is None:
            return self.value
        if self.coerce == 'bool':
            if self.value in COERCE_FALSE_VALS:
                return False
            return True
        if self.coerce == 'int':
            return int(self.value)
    
    class Meta:
        abstract = True


def get_coercion_from_form(form):
    """
    This generates a dictionary of key names to types 
    for the inputted form. This is useful in the 'coercion' 
    attribute of the set saved values function.
    """
    coercion = {}
    for k, f in form.base_fields.items():
        if isinstance(f, fields.IntegerField):
            coercion.update({k:'int'})
        elif isinstance(f, fields.BooleanField):
            coercion.update({k:'bool'})
    return coercion

def set_saved_values(dictionary, to=SavedValue, narrow=None, coercion=None):
    """
    Saves form data to saved settings models. The 
    narrow parameter is used to limit the replacement 
    and update selection as well as default some values.
    """
    for k,v in dictionary.items():
        coerce = coercion.get(k, None) if coercion else None
        filter = {'key': k}
        filter.update(narrow or {})
        if v is not None and v != '':
            val = unicode(v)
            if isinstance(v, Model):
                val = v.pk

            try:
                to.objects.get(**filter)
                to.objects.filter(**filter).update(value=val, coerce=coerce)
            except to.DoesNotExist:
                to.objects.create(value=val, coerce=coerce, **filter)
            except MultipleObjectsReturned:
                raise Exception('Multiple objects where returned during the get step of saving. This means your narrow parameter is not sufficient.')
        else:
            to.objects.filter(**filter).delete()

def get_saved_values(frm=SavedValue, narrow=None):
    return dict([(v.key, v.final) for v in frm.objects.filter(**narrow)])
