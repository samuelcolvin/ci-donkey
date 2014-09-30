# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buildinfo',
            name='main_log',
        ),
        migrations.RemoveField(
            model_name='buildinfo',
            name='pre_log',
        ),
        migrations.AddField(
            model_name='buildinfo',
            name='container_exists',
            field=models.BooleanField(default=False, verbose_name=b'container exists'),
            preserve_default=True,
        ),
    ]
