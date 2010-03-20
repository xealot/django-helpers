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
            field = self.key_to_field_id[k]
            filter = {'key': k, 'field': field}
            filter.update(narrow or {})
            if v is not None and v != '':
                try:
                    to.objects.get(**filter)
                    if field.type.pk == 6: #Image Field
                        to.objects.filter(**filter).update(value=str(v), blob=v.file)
                    else:
                        to.objects.filter(**filter).update(value=str(v))
                except to.DoesNotExist:
                    if field.type_id == 6: #Image Field
                        to.objects.create(value=str(v), blob=v.file, **filter)
                    else:
                        to.objects.create(value=str(v), **filter)
                except MultipleObjectsReturned:
                    raise Exception('Multiple objects where returned during the get step of saving. This means your narrow parameter is not sufficient.')
            else:
                to.objects.filter(**filter).delete()
