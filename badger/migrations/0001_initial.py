# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import badger.models
from django.conf import settings
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(help_text=b'Explanation and evidence for the badge award', blank=True)),
                ('image', models.ImageField(storage=django.core.files.storage.FileSystemStorage(base_url=b'uploads/', location=b'uploads'), null=True, upload_to=badger.models.UploadTo(b'image', b'png'), blank=True)),
                ('claim_code', models.CharField(default=b'', help_text=b'Code used to claim this award', max_length=32, db_index=True, blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-modified', '-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Short, descriptive title', unique=True, max_length=255)),
                ('slug', models.SlugField(help_text=b'Very short name, for use in URLs and links', unique=True)),
                ('description', models.TextField(help_text=b'Longer description of the badge and its criteria', blank=True)),
                ('image', models.ImageField(help_text=b'Upload an image to represent the badge', storage=django.core.files.storage.FileSystemStorage(base_url=b'uploads/', location=b'uploads'), null=True, upload_to=badger.models.UploadTo(b'image', b'png'), blank=True)),
                ('unique', models.BooleanField(default=True, help_text=b'Should awards of this badge be limited to one-per-person?')),
                ('nominations_accepted', models.BooleanField(default=True, help_text=b'Should this badge accept nominations from other users?')),
                ('nominations_autoapproved', models.BooleanField(default=False, help_text=b'Should all nominations be automatically approved?')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('prerequisites', models.ManyToManyField(help_text=b'When all of the selected badges have been awarded, this badge will be automatically awarded.', to='badger.Badge', null=True, blank=True)),
            ],
            options={
                'ordering': ['-modified', '-created'],
                'permissions': (('manage_deferredawards', 'Can manage deferred awards for this badge'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeferredAward',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(blank=True)),
                ('reusable', models.BooleanField(default=False)),
                ('email', models.EmailField(db_index=True, max_length=75, null=True, blank=True)),
                ('claim_code', models.CharField(default=badger.models.make_random_code, unique=True, max_length=32, db_index=True)),
                ('claim_group', models.CharField(db_index=True, max_length=32, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('badge', models.ForeignKey(to='badger.Badge')),
                ('creator', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-modified', '-created'],
                'permissions': (('grant_deferredaward', 'Can grant deferred award to an email address'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Nomination',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('accepted', models.BooleanField(default=False)),
                ('rejected_reason', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('approver', models.ForeignKey(related_name='nomination_approver', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('award', models.ForeignKey(blank=True, to='badger.Award', null=True)),
                ('badge', models.ForeignKey(to='badger.Badge')),
                ('creator', models.ForeignKey(related_name='nomination_creator', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('nominee', models.ForeignKey(related_name='nomination_nominee', to=settings.AUTH_USER_MODEL)),
                ('rejected_by', models.ForeignKey(related_name='nomination_rejected_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('percent', models.FloatField(default=0)),
                ('counter', models.FloatField(default=0, null=True, blank=True)),
                ('notes', badger.models.JSONField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('badge', models.ForeignKey(to='badger.Badge')),
                ('user', models.ForeignKey(related_name='progress_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Progresses',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='progress',
            unique_together=set([('badge', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='badge',
            unique_together=set([('title', 'slug')]),
        ),
        migrations.AddField(
            model_name='award',
            name='badge',
            field=models.ForeignKey(to='badger.Badge'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='award',
            name='creator',
            field=models.ForeignKey(related_name='award_creator', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='award',
            name='user',
            field=models.ForeignKey(related_name='award_user', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
