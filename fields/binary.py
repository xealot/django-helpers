from django.db.models.fields import Field
from django.forms import fields as form_fields

#Add south migration rules.
try:
    from south.modelsinspector import add_introspection_rules
    #:TODO: This is hardcoded, I need to figure the path to this class dynamically. A partial RE doesn't seem to work
    add_introspection_rules([], ["helpers\.dh\.fields\.binary\.BlobField"])
    add_introspection_rules([], ["helpers\.dh\.fields\.binary\.BinaryField"])
    add_introspection_rules([], ["helpers\.dh\.fields\.binary\.InlineImageField"])
except ImportError:
    pass


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
