# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Form'
        db.create_table('form_designer_form', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('config_json', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('form_designer', ['Form'])

        # Adding model 'FormField'
        db.create_table('form_designer_formfield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fields', to=orm['form_designer.Form'])),
            ('ordering', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('choices', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('help_text', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('default_value', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('is_required', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('form_designer', ['FormField'])

        # Adding unique constraint on 'FormField', fields ['form', 'name']
        db.create_unique('form_designer_formfield', ['form_id', 'name'])

        # Adding model 'FormSubmission'
        db.create_table('form_designer_formsubmission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('submitted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['form_designer.Form'])),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('form_designer', ['FormSubmission'])

    def backwards(self, orm):
        
        # Removing unique constraint on 'FormField', fields ['form', 'name']
        db.delete_unique('form_designer_formfield', ['form_id', 'name'])

        # Deleting model 'Form'
        db.delete_table('form_designer_form')

        # Deleting model 'FormField'
        db.delete_table('form_designer_formfield')

        # Deleting model 'FormSubmission'
        db.delete_table('form_designer_formsubmission')

    models = {
        'form_designer.form': {
            'Meta': {'object_name': 'Form'},
            'config_json': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'form_designer.formfield': {
            'Meta': {'ordering': "['ordering', 'id']", 'unique_together': "(('form', 'name'),)", 'object_name': 'FormField'},
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'default_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fields'", 'to': "orm['form_designer.Form']"}),
            'help_text': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'form_designer.formsubmission': {
            'Meta': {'ordering': "('-submitted',)", 'object_name': 'FormSubmission'},
            'data': ('django.db.models.fields.TextField', [], {}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['form_designer.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'submitted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['form_designer']
