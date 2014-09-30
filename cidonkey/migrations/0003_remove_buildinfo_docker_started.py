# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0002_auto_20140930_2005'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buildinfo',
            name='docker_started',
        ),
    ]
