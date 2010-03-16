from django.db.models.fields import Field
from django.forms import fields as form_fields


class BinaryField(Field):
    """Sometimes we have fields that need to store a small amount of binary
    data. This is different then a varchar on postgresql at least because it
    will not allow fields that are just null bytes.
    """

    def get_internal_type(self):
        return 'BinaryField'

    def get_prep_value(self, value):
        if type(value) == buffer:
            return value
        if hasattr(value, 'read'):
            return buffer(value.read())
        return None


class BlobField(Field):
    """Sometimes we have fields that need to store a large amounts of binary
    data. 
    """
    def get_internal_type(self):
        return 'BlobField'

    def get_prep_value(self, value):
        if type(value) == buffer:
            return value
        if hasattr(value, 'read'):
            return buffer(value.read())
        return None


class InlineImageField(BlobField):
    def formfield(self, **kwargs):
        defaults = {'form_class': form_fields.ImageField}
        defaults.update(kwargs)
        return super(InlineImageField, self).formfield(**defaults)
