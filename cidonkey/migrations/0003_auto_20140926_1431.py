# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0002_auto_20140923_1918'),
    ]

    operations = [
        migrations.AddField(
            model_name='build',
            name='container_id',
            field=models.CharField(default='xxx', max_length=100, verbose_name=b'container ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='build',
            name='complete',
            field=models.BooleanField(default=False, verbose_name=b'processing complete'),
        ),
    ]
