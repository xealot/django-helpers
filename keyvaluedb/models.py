from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from ..fields.binary import BlobField

class SavedValue(models.Model):
    key = models.SlugField(max_length=100, editable=False)
    value = models.TextField(null=True, blank=True)
    blob = BlobField(null=True, blank=True)
    
    class Meta:
        abstract = True


def set_saved_values(dictionary, to=SavedValue, narrow=None):
    """
    Saves form data to saved settings models. The 
    narrow parameter is used to limit the replacement 
    and update selection as well as default some values.
    """
    for k,v in dictionary.items():
        filter = {'key': k}
        filter.update(narrow or {})
        if v is not None and v != '':
            try:
                to.objects.get(**filter)
                to.objects.filter(**filter).update(value=str(v))
            except to.DoesNotExist:
                to.objects.create(value=str(v), **filter)
            except MultipleObjectsReturned:
                raise Exception('Multiple objects where returned during the get step of saving. This means your narrow parameter is not sufficient.')
        else:
            to.objects.filter(**filter).delete()

def get_saved_values(frm=SavedValue, narrow=None):
    return dict(frm.objects.filter(**narrow).values_list('key', 'value'))
