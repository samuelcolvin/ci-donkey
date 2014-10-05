# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0004_buildinfo_container_inspection'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='coverage_regex',
            field=models.CharField(default=b'\nOVERALL COVERAGE = ([\\d\\.]+)%\n', max_length=500, blank=True, help_text=b'regular expression to use to search for overage value, should have one group with can be parsed as a float.', null=True, verbose_name=b'coverage regex'),
            preserve_default=True,
        ),
    ]
