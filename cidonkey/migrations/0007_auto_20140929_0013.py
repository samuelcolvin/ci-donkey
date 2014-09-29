# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0006_auto_20140928_1156'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='allow_repeat',
            field=models.BooleanField(default=False, help_text=b'Allow repeat builds for the same sha.', verbose_name=b'allow_repeats'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_branch',
            field=models.CharField(default=b'master', max_length=50, verbose_name=b'default branch'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='webhook_secret',
            field=models.CharField(default='asdfsafdsf', max_length=100, verbose_name=b'webhook secret'),
            preserve_default=False,
        ),
    ]
