from django.db import models
from ..utilities import slugify
from ..fields.json import JSONField
from ..fields.binary import BlobField


class FieldType(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class FormDef(models.Model):
    name = models.CharField(max_length=100)
    success_msg = models.CharField(max_length=250, null=True, blank=True, verbose_name="Success Message")
    failure_msg = models.CharField(max_length=250, null=True, blank=True, verbose_name="Failure Message")

    def create_form(self, querysets=None):
        from utilities import dbform_factory #Avoid circular import
        return dbform_factory(self, querysets)

    def __unicode__(self):
        return self.name


class Field(models.Model):
    form = models.ForeignKey('FormDef', editable=False)
    type = models.ForeignKey('FieldType', verbose_name="Field Type to Show",
                             help_text="The type of form field the system should associate with this variable.")
    name = models.CharField(max_length=100, verbose_name="Field Name")
    #verbose_name = models.CharField(max_length=100, verbose_name="Long name for Field")
    field_data = models.CharField(max_length=1000, blank=True, null=True, verbose_name="Field Data Definition", 
                                  help_text="If the type of field you chose above has a data requirement, this is where it is defined.")
    nonfield_data = JSONField(blank=True, null=True, verbose_name="Extra data for internal use")
    html_attr = models.CharField(max_length=1000, blank=True, null=True, verbose_name="Html Attributes",
                                 help_text='Include html attributes when rendering this field. The most common example are CSS class attributes.')
    key = models.SlugField(max_length=100, editable=False)
    default = models.TextField(blank=True, null=True, verbose_name="Default value for Field",
                               help_text="The default value to use if this variable is not set by the user. This can either be a literal string such as 'A Value' or an expression of the form '=<context>.<key>' (e.g. =profile.name)")
    required = models.BooleanField(default=False, help_text='This field is required for the form to be saved.')
    editable = models.BooleanField(default=True, verbose_name="Is this Field Editable")
    help_text = models.TextField(blank=True, null=True, verbose_name="Optional Help Text to be shown during edit")
    priority = models.IntegerField(default=50, verbose_name="Field Display Priority", 
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
            self.key = slugify(self.name)
            super(Field, self).save(**kwargs)
            

class SavedValue(models.Model):
    field = models.ForeignKey('Field')
    key = models.SlugField(max_length=100, editable=False)
    value = models.TextField(null=True, blank=True)
    blob = BlobField(null=True, blank=True)
    
    class Meta:
        abstract = True












