# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0003_remove_buildinfo_docker_started'),
    ]

    operations = [
        migrations.AddField(
            model_name='buildinfo',
            name='container_inspection',
            field=models.TextField(null=True, verbose_name=b'container inspection', blank=True),
            preserve_default=True,
        ),
    ]
