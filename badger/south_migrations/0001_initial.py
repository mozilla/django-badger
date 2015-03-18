# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Badge'
        db.create_table('badger_badge', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('badger', ['Badge'])

        # Adding unique constraint on 'Badge', fields ['title', 'slug']
        db.create_unique('badger_badge', ['title', 'slug'])

        # Adding M2M table for field prerequisites on 'Badge'
        db.create_table('badger_badge_prerequisites', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_badge', models.ForeignKey(orm['badger.badge'], null=False)),
            ('to_badge', models.ForeignKey(orm['badger.badge'], null=False))
        ))
        db.create_unique('badger_badge_prerequisites', ['from_badge_id', 'to_badge_id'])

        # Adding model 'Award'
        db.create_table('badger_award', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('badge', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['badger.Badge'])),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='award_user', to=orm['auth.User'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='award_creator', null=True, to=orm['auth.User'])),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('badger', ['Award'])

        # Adding model 'Progress'
        db.create_table('badger_progress', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('badge', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['badger.Badge'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='progress_user', to=orm['auth.User'])),
            ('percent', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('counter', self.gf('django.db.models.fields.FloatField')(default=0, null=True, blank=True)),
            ('notes', self.gf('badger.models.JSONField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('badger', ['Progress'])

        # Adding unique constraint on 'Progress', fields ['badge', 'user']
        db.create_unique('badger_progress', ['badge_id', 'user_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Progress', fields ['badge', 'user']
        db.delete_unique('badger_progress', ['badge_id', 'user_id'])

        # Removing unique constraint on 'Badge', fields ['title', 'slug']
        db.delete_unique('badger_badge', ['title', 'slug'])

        # Deleting model 'Badge'
        db.delete_table('badger_badge')

        # Removing M2M table for field prerequisites on 'Badge'
        db.delete_table('badger_badge_prerequisites')

        # Deleting model 'Award'
        db.delete_table('badger_award')

        # Deleting model 'Progress'
        db.delete_table('badger_progress')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'badger.award': {
            'Meta': {'object_name': 'Award'},
            'badge': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['badger.Badge']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'award_creator'", 'null': 'True', 'to': "orm['auth.User']"}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_user'", 'to': "orm['auth.User']"})
        },
        'badger.badge': {
            'Meta': {'unique_together': "(('title', 'slug'),)", 'object_name': 'Badge'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'prerequisites': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['badger.Badge']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'badger.progress': {
            'Meta': {'unique_together': "(('badge', 'user'),)", 'object_name': 'Progress'},
            'badge': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['badger.Badge']"}),
            'counter': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('badger.models.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'percent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'progress_user'", 'to': "orm['auth.User']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['badger']
