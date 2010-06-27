from django.forms.forms import BaseForm
from django.forms.fields import ImageField
from django.core.exceptions import MultipleObjectsReturned, ValidationError

BLOB_SIZE_LIMIT = 128000

class ImageSizeLimitedField(ImageField):
    def validate(self, value):
        super(ImageSizeLimitedField, self).validate(value)
        if value and value.size > BLOB_SIZE_LIMIT:
            raise ValidationError('Please limit the image to 125KB in size. Your image was larger than this.')

class DBForm(BaseForm):
    #:TODO: on save this should look at default avlues, if they match REMOVE the entry.
    def save(self, to, narrow=None, skip_initial=True):
        """
        Saves form data to saved settings models. The 
        narrow parameter is used to limit the replacement 
        and update selection as well as default some values.
        
        skip_initial: If the to save value matches the initial 
        value on the form skip saving or updating this value.
        """
        from helpers.dh.dbform.utilities import TYPE_IMAGE #Avoid circular import

        dictionary = self.cleaned_data
        for k,v in dictionary.items():
            field = self.key_to_field_id[k]
            filter = {'key': k, 'field': field}
            filter.update(narrow or {})
            if skip_initial and self.initial.get(k, None) == v:
                continue
            if v is not None and v != '':
                try:
                    to.objects.get(**filter)
                    if field.type_id == TYPE_IMAGE: #Image Field
                        to.objects.filter(**filter).update(value=str(v), blob=v.file)
                    else:
                        to.objects.filter(**filter).update(value=str(v))
                except to.DoesNotExist:
                    if field.type_id == TYPE_IMAGE: #Image Field
                        to.objects.create(value=str(v), blob=v.file, **filter)
                    else:
                        to.objects.create(value=str(v), **filter)
                except MultipleObjectsReturned:
                    raise Exception('Multiple objects where returned during the get step of saving. This means your narrow parameter is not sufficient.')
            else:
                to.objects.filter(**filter).delete()
