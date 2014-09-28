# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cidonkey.models


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0005_auto_20140926_1718'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='buildinfo',
            options={'ordering': ['-id'], 'verbose_name': 'Build', 'verbose_name_plural': 'Builds'},
        ),
        migrations.AddField(
            model_name='buildinfo',
            name='docker_started',
            field=models.BooleanField(default=False, verbose_name=b'docker started'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='action',
            field=models.CharField(max_length=20, null=True, verbose_name=b'action', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='archive',
            field=models.FileField(null=True, upload_to=cidonkey.models.archive_dir, blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='author',
            field=models.CharField(max_length=100, null=True, verbose_name=b'author', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='commit_message',
            field=models.CharField(max_length=200, null=True, verbose_name=b'commit message', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='complete',
            field=models.BooleanField(default=False, verbose_name=b'complete'),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='container',
            field=models.CharField(max_length=100, null=True, verbose_name=b'container ID', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='coverage',
            field=models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='display_url',
            field=models.URLField(null=True, verbose_name=b'display URL', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='fetch_branch',
            field=models.CharField(max_length=200, null=True, verbose_name=b'fetch branch name', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='fetch_cmd',
            field=models.CharField(max_length=200, null=True, verbose_name=b'fetch command', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='finished',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='label',
            field=models.CharField(max_length=200, null=True, verbose_name=b'branch label', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='main_log',
            field=models.TextField(null=True, verbose_name=b'main build log', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name=b'last modified'),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='pre_log',
            field=models.TextField(null=True, verbose_name=b'pre build log', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='sha',
            field=models.CharField(max_length=50, null=True, verbose_name=b'commit sha', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='status_url',
            field=models.URLField(null=True, verbose_name=b'status URL', blank=True),
        ),
        migrations.AlterField(
            model_name='buildinfo',
            name='temp_dir',
            field=models.CharField(max_length=100, null=True, verbose_name=b'temporary directory', blank=True),
        ),
    ]
