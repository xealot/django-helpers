from django.forms.forms import BaseForm
from django.core.exceptions import MultipleObjectsReturned

class DBForm(BaseForm):
    def save(self, to, narrow=None):
        """
        Saves form data to saved settings models. The 
        narrow parameter is used to limit the replacement 
        and update selection as well as default some values.
        """
        dictionary = self.cleaned_data
        for k,v in dictionary.items():
            if v is not None and v != '':
                filter = {'key': k, 'field': self.key_to_field_id[k]}
                filter.update(narrow or {})
                try:
                    to.objects.get(**filter)
                    to.objects.filter(**filter).update(value=str(v))
                except to.DoesNotExist:
                    to.objects.create(value=str(v), **filter)
                except MultipleObjectsReturned:
                    raise Exception('Multiple objects where returned during the get step of saving. This means your narrow parameter is not sufficient.')
            else:
                to.objects.filter(name=k).delete()
