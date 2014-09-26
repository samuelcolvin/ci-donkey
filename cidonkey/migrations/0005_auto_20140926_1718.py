# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0004_auto_20140926_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buildinfo',
            name='finished',
            field=models.DateTimeField(null=True),
        ),
    ]
