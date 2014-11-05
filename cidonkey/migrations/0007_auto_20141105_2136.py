# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0006_auto_20141105_2057'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buildinfo',
            name='start',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
