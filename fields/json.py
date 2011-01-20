#####David Cramers Updated Version::http://www.davidcramer.net/code/448/cleaning-up-with-json-and-sql.html
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django import forms
from django.db import models

#Add south migration rules.
try:
    from south.modelsinspector import add_introspection_rules
    #:TODO: This is hardcoded, I need to figure the path to this class dynamically.
    add_introspection_rules([], ["helpers\.dh\.fields\.json\.JSONField"])
except ImportError:
    pass


class JSONWidget(forms.Textarea):
    def render(self, name, value, attrs=None):
        if not isinstance(value, basestring):
            value = json.dumps(value, indent=2)
        return super(JSONWidget, self).render(name, value, attrs)
 
class JSONFormField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = JSONWidget
        super(JSONFormField, self).__init__(*args, **kwargs)
 
    def clean(self, value):
        if not value: return
        try:
            return json.loads(value)
        except Exception, exc:
            raise forms.ValidationError(u'JSON decode error: %s' % (unicode(exc),))
 
class JSONField(models.TextField):
    __metaclass__ = models.SubfieldBase
 
    def formfield(self, **kwargs):
        return super(JSONField, self).formfield(form_class=JSONFormField, **kwargs)
 
    def to_python(self, value):
        if isinstance(value, basestring) and value != '':
#            try:
#                return json.loads(value)
#            except ValueError:
#                pass
            value = json.loads(value)
        return value
 
    def get_db_prep_save(self, connection, value):
        if value is None: return
        return json.dumps(value)
 
    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


#class JSONField(models.TextField):
#    """JSONField is a generic textfield that neatly serializes/unserializes
#    JSON objects seamlessly"""
#
#    # Used so to_python() is called
#    __metaclass__ = models.SubfieldBase
#
#    def to_python(self, value):
#        """Convert our string value to JSON after we load it from the DB"""
#
#        if value == "":
#            return None
#
#        try:
#            if isinstance(value, basestring):
#                return json.loads(value)
#        except ValueError:
#            pass
#
#        return value
#
#    def get_db_prep_save(self, value):
#        """Convert our JSON object to a string before we save"""
#        if value == "":
#            return None
#
#        if isinstance(value, dict):
#            value = json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False)
#
#        return super(JSONField, self).get_db_prep_save(value)
