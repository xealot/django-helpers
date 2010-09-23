# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'FieldType'
        db.create_table('dbform_fieldtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('dbform', ['FieldType'])

        # Adding model 'FormDef'
        db.create_table('dbform_formdef', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('dbform', ['FormDef'])

        # Adding model 'Field'
        db.create_table('dbform_field', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dbform.FormDef'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dbform.FieldType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('field_data', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
            ('nonfield_data', self.gf('helpers.dh.fields.json.JSONField')(null=True, blank=True)),
            ('html_attr', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
            ('key', self.gf('django.db.models.fields.SlugField')(max_length=100, db_index=True)),
            ('default', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('help_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=50)),
        ))
        db.send_create_signal('dbform', ['Field'])

        # Adding unique constraint on 'Field', fields ['key', 'form']
        db.create_unique('dbform_field', ['key', 'form_id'])


    def backwards(self, orm):
        
        # Deleting model 'FieldType'
        db.delete_table('dbform_fieldtype')

        # Deleting model 'FormDef'
        db.delete_table('dbform_formdef')

        # Deleting model 'Field'
        db.delete_table('dbform_field')

        # Removing unique constraint on 'Field', fields ['key', 'form']
        db.delete_unique('dbform_field', ['key', 'form_id'])


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dbform.field': {
            'Meta': {'ordering': "('-priority', 'name')", 'unique_together': "(('key', 'form'),)", 'object_name': 'Field'},
            'default': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'field_data': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbform.FormDef']"}),
            'help_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'html_attr': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'nonfield_data': ('helpers.dh.fields.json.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '50'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbform.FieldType']"})
        },
        'dbform.fieldtype': {
            'Meta': {'object_name': 'FieldType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dbform.formdef': {
            'Meta': {'object_name': 'FormDef'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['dbform']
