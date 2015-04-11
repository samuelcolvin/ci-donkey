# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0008_buildinfo_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buildinfo',
            name='commit_message',
            field=models.CharField(max_length=1013, null=True, verbose_name=b'commit message', blank=True),
        ),
    ]
