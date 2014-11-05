# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0005_project_coverage_regex'),
    ]

    operations = [
        migrations.AddField(
            model_name='buildinfo',
            name='queued',
            field=models.BooleanField(default=False, verbose_name=b'queued'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='update_url',
            field=models.CharField(default=b'unknown', max_length=200, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='project',
            name='webhook_secret',
            field=models.CharField(max_length=100, editable=False),
        ),
    ]
