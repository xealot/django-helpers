import hashlib, functools, time
from cgi import parse_qs
from django import forms
from django.db import models
from django.utils import simplejson as json
from django.template import Context, Template
from django.forms.util import flatatt
from django.forms.forms import BaseForm
from django.forms.fields import ImageField
from django.forms.widgets import FileInput
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe

from utilities import resolve_default

BLOB_SIZE_LIMIT = 128000

TYPE_TEXT = 1
TYPE_CHOICE = 2
TYPE_DB_ENTITY = 3
TYPE_LARGE_TEXT = 4
TYPE_BOOL = 5
TYPE_IMAGE = 6


class ExistingImageWidget(FileInput):
    def __init__(self, image_url=None, initial=None, height=125, *args, **kwargs):
        self.image_url = image_url
        self.height = height
        self.initial = initial
        super(ExistingImageWidget, self).__init__(*args, **kwargs)

    def value_from_datadict(self, data, files, name):
        value = files.get(name, None)
        value = value or data.get(name, None)
        return value

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        hidden_atts = final_attrs.copy()
        hidden_atts.update(type='hidden', value='--remove--', disabled='disabled')
        
        attrs = final_attrs.copy()
        attrs.update(image_url=self.image_url, 
                     height=self.height, 
                     flat_atts=flatatt(final_attrs), 
                     hidden_atts=flatatt(hidden_atts),
                     rand=time.time())
        
        if self.image_url and value and value != self.initial:
            return mark_safe(u'''
            <div id="dbfi_%(id)s" class="dbfi">
                <div class="dbfi_display">
                    <span id="dbfi_%(id)s_show" class="dbfi_action"><img src="%(image_url)s?rand=%(rand)s" height="%(height)s" alt="Image"/></span>
                    <span id="dbfi_%(id)s_change" class="dbfi_action" style="display:none;"><input%(flat_atts)s /></span>
                    <span id="dbfi_%(id)s_delete" class="dbfi_action" style="display:none;"><span style="background-color: lightyellow; padding: 3px;">Your image will be removed on submit.</span><input%(hidden_atts)s /></span>
                </div>
                <div class="dbfi_choices">
                    <a href="#dbfi_%(id)s_change">Change</a> | <a href="#dbfi_%(id)s_delete">Delete</a>
                </div>
                <div class="dbfi_cancel" style="display:none;">
                    <a href="#dbfi_%(id)s_show">Cancel</a>
                </div>
            </div>
            ''' % attrs)
        return super(ExistingImageWidget, self).render(name, None, attrs=attrs)


class ExistingImageField(ImageField):
    def __init__(self, image_resolver=None, *args, **kwargs):
        super(ExistingImageField, self).__init__(*args, **kwargs)
        self.widget = ExistingImageWidget(image_resolver and image_resolver() or None, initial=kwargs.get('initial', None))

#    def to_python(self, data):
#        if isinstance(data, basestring):
#            return data
#        return super(ExistingImageField, self).to_python(data)

    def clean(self, data, initial=None):
        if data and isinstance(data, basestring):
            return data
        if not data and initial:
            return initial
        return super(ExistingImageField, self).clean(data)
        
    def validate(self, value):
        super(ExistingImageField, self).validate(value)
        if value and value.size > BLOB_SIZE_LIMIT:
            raise ValidationError('Please limit the image to 125KB in size. Your image was larger than this.')


def parse_field_data(data):
    field_data = []
    for row in data.split('\n'):
        row = row.strip()
        label, _, value = row.partition('|')
        field_data.append((value.strip(), label.strip()))
    return field_data


class DBForm(BaseForm):
    """
    This for class is geared to reading and writing from the dbform application. It also has some special cases 
    for handling images in a less than completely idiotic way.
    """

    @staticmethod
    def create(formdef, context, querysets=None, image_resolver=None):
        """Take a FormDef instance and create a real django form out of it"""
        base_fields = SortedDict()
        key_to_field_id = {} #This is so the save function on DBForm has enough information to save
        for field in formdef.field_set.select_related():
            key_to_field_id[field.key] = field
            if field.editable is False:
                continue
            default_args = {'required': field.required, 'help_text': resolve_default(context, field.help_text), 
                            'label': resolve_default(context, field.label), 'initial': field.default}
            if field.type_id == TYPE_CHOICE:
                choices = parse_field_data(resolve_default(context, field.field_data))
                base_fields[field.key] = forms.ChoiceField(choices=choices, widget=forms.RadioSelect, **default_args)
            elif field.type_id == TYPE_DB_ENTITY:
                if querysets is not None and field.key in querysets:
                    qs = querysets[field.key]
                else:
                    app_label, model_name = field.field_data.split('.')
                    Model = models.get_model(app_label, model_name)
                    qs = Model.objects.all()
                base_fields[field.key] = forms.ModelChoiceField(qs, **default_args)
            elif field.type_id == TYPE_BOOL:
                base_fields[field.key] = forms.BooleanField(widget=forms.RadioSelect(choices=((True, 'Yes'),(False, 'No'))), **default_args)
            elif field.type_id == TYPE_IMAGE:
                ir = callable(image_resolver) and functools.partial(image_resolver, field.key) or None 
                base_fields[field.key] = ExistingImageField(image_resolver=ir, **default_args)
            elif field.type_id == TYPE_LARGE_TEXT:
                base_fields[field.key] = forms.CharField(widget=forms.Textarea(attrs={'class': 'wysiwyg'}), **default_args)
            else:
                base_fields[field.key] = forms.CharField(max_length=100, **default_args)
    
            #Apply HTML attributes to widget.attrs
            final_attrs = {}
            if field.html_attr:
                attrs = parse_qs(field.html_attr, keep_blank_values=True)
                #I'm making the assumption here that since these are HTML attributes that lists should be combined with ' '
                for k,v in attrs.items():
                    final_attrs[k] = ' '.join(v)
    
            #USE WITH jquery.metadata -- Apply non-field data as css attribute as well; this is separate because they service separate purposes.
            if field.nonfield_data:
                value = json.dumps(field.nonfield_data).replace('"', "'")
                if 'class' in final_attrs:
                    final_attrs['class'] += ' %s' % value
                else:
                    final_attrs['class'] = value
            base_fields[field.key].widget.attrs.update(final_attrs)
        DBFormClass = type(str('%sDBForm' % formdef.name), (DBForm,), {'base_fields':base_fields, 'key_to_field_id': key_to_field_id})
        return DBFormClass
    
    #:TODO: on save this should look at default avlues, if they match REMOVE the entry.
    def save(self, to, narrow=None, skip_initial=True):
        """
        Saves form data to saved settings models. The 
        narrow parameter is used to limit the replacement 
        and update selection as well as default some values.
        
        skip_initial: If the to save value matches the initial 
        value on the form skip saving or updating this value.
        """
        dictionary = self.cleaned_data
        for k, v in dictionary.items():
            field = self.key_to_field_id[k]
            filter = {'key': k, 'field': field}
            filter.update(narrow or {})
            if skip_initial and self.initial.get(k, None) == v:
                continue
            try:
                if v is None or v == '':
                    to.objects.filter(**filter).delete()
                    continue
                to.objects.get(**filter)
                if field.type_id == TYPE_IMAGE: #Image Field
                    if isinstance(v, basestring) and v == '--remove--':
                        to.objects.filter(**filter).delete()
                        continue
                    value = hashlib.sha224(unicode(v.file)).hexdigest()
                    to.objects.filter(**filter).update(value=value, blob=v.file)
                else:
                    to.objects.filter(**filter).update(value=unicode(v))
            except to.DoesNotExist:
                if field.type_id == TYPE_IMAGE: #Image Field
                    if isinstance(v, basestring) and v == '--remove--':
                        to.objects.filter(**filter).delete()
                        continue
                    value = hashlib.sha224(unicode(v.file)).hexdigest()
                    to.objects.create(value=value, blob=v.file, **filter)
                else:
                    to.objects.create(value=unicode(v), **filter)
            except MultipleObjectsReturned:
                raise Exception('Multiple objects where returned during the get step of saving. This means your narrow parameter is not sufficient.')
