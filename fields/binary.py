"""
Caution, introspection will not work unless a custom backend is also provided.
"""
from django.db.models.fields import Field
from django.db.models import SubfieldBase
from django.forms import fields as form_fields

try:
    import cStringIO
    from cStringIO import StringIO
    S_TYPES = (cStringIO.InputType, cStringIO.OutputType)
except ImportError:
    from StringIO import StringIO
    S_TYPES = (StringIO,)

#Add south migration rules.
try:
    from south.modelsinspector import add_introspection_rules
    #:TODO: This is hardcoded, I need to figure the path to this class dynamically. A partial RE doesn't seem to work
    add_introspection_rules([], ["helpers\.dh\.fields\.binary\.BlobField"])
    add_introspection_rules([], ["helpers\.dh\.fields\.binary\.BinaryField"])
    add_introspection_rules([], ["helpers\.dh\.fields\.binary\.InlineImageField"])
except ImportError:
    pass

class BinaryFieldBase(Field):
    __metaclass__ = SubfieldBase
    def to_python(self, value):
        if isinstance(value, S_TYPES):
            return value
        if value is None:
            return StringIO()
        return StringIO(value)

    def get_prep_value(self, value):
        if hasattr(value, 'read'):
            value = value.read()
        if len(value) == 0:
            value = None
        print 'DB PREP2', type(value)
        return value

    def get_prep_lookup(self, lookup_type, value):
        raise TypeError('Binary Fields do not support %s' % lookup_type)
    
class BinaryField(BinaryFieldBase):
    """Sometimes we have fields that need to store a small amount of binary
    data. This is different then a varchar on postgresql at least because it
    will not allow fields that are just null bytes.
    """
    def __init__(self, max_length, *args, **kwargs):
        self.max_length = max_length
        super(BinaryField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'varbinary(%(max_length)s)' % self.max_length
        else:
            raise Exception('Mysql is the only defined engine for BinaryField.')


class BlobField(BinaryFieldBase):
    """Sometimes we have fields that need to store a large amounts of binary
    data. 
    """
    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'longblob'
        else:
            raise Exception('Mysql is the only defined engine for BlobField.')


class InlineImageField(BlobField):
    def formfield(self, **kwargs):
        defaults = {'form_class': form_fields.ImageField}
        defaults.update(kwargs)
        return super(InlineImageField, self).formfield(**defaults)
