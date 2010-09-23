from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from ..utilities import slugify
from ..fields.json import JSONField
from ..fields.binary import BlobField
from ..keyvaluedb.models import SavedValue as KVDBValues


class FieldType(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class FormDef(models.Model):
    """
    This model cannot be abstract because the reference from 
    Field requires a concrete model.
    """
    name = models.CharField(max_length=100)
    #success_msg = models.CharField(max_length=250, null=True, blank=True, verbose_name="Success Message")
    #failure_msg = models.CharField(max_length=250, null=True, blank=True, verbose_name="Failure Message")
    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.PositiveIntegerField(editable=False)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def create_form(self, querysets=None):
        from utilities import dbform_factory #Avoid circular import
        return dbform_factory(self, querysets)

    def __unicode__(self):
        return self.name


class Field(models.Model):
    form = models.ForeignKey('FormDef', editable=False)
    type = models.ForeignKey('FieldType', verbose_name="Field Type",
                             help_text="The type of form field the system should associate with this variable.")
    name = models.CharField(max_length=100, verbose_name="Name")
    #verbose_name = models.CharField(max_length=100, verbose_name="Long name for Field")
    field_data = models.TextField(max_length=1000, blank=True, null=True, verbose_name="Extra Data", 
                                  help_text="Based on the field type chosen you may need to enter data in this field. (e.g. If this field type is a choice field, choices would go here)")
    nonfield_data = JSONField(blank=True, null=True, verbose_name="Extra data for internal use")
    html_attr = models.CharField(max_length=1000, blank=True, null=True, verbose_name="Html Attributes",
                                 help_text='Include html attributes when rendering this field. The most common example are CSS class attributes.')
    key = models.SlugField(max_length=100, editable=False)
    default = models.TextField(blank=True, null=True, verbose_name="Default Value",
                               help_text="The default value to use if this variable is not set by the user. This can either be a literal string such as 'A Value' or an expression of the form '{{variable_name}}' (e.g. {{profile.name}})")
    required = models.BooleanField(default=False, help_text='This field is required for the form to be saved.')
    editable = models.BooleanField(default=True, verbose_name="Editable", help_text="This determines if this field will show up when the users is editing this form.")
    help_text = models.TextField(blank=True, null=True, verbose_name="Instructions & Help")
    priority = models.IntegerField(default=50, verbose_name="Display Priority", 
                                   help_text="The higher the number the closer to the top this field will be. When these settings are displayed the highest priorities will go first.")

    class Meta:
        unique_together = ('key', 'form')
        ordering = ('-priority', 'name')
    
    def __unicode__(self):
        return self.name

    @property
    def label(self):
        #if self.verbose_name:
        #    return self.verbose_name
        return self.name

    def save(self, **kwargs):
        if not self.key:
            self.key = slugify(self.name)
        super(Field, self).save(**kwargs)
            

class SavedValue(KVDBValues):
    field = models.ForeignKey('Field')
    
    class Meta:
        abstract = True












