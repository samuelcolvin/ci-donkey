# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cidonkey.models


class Migration(migrations.Migration):

    dependencies = [
        ('cidonkey', '0003_auto_20140926_1431'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sha', models.CharField(max_length=50, null=True, verbose_name=b'commit sha')),
                ('trigger', models.CharField(max_length=20, verbose_name=b'trigger')),
                ('action', models.CharField(max_length=20, null=True, verbose_name=b'action')),
                ('label', models.CharField(max_length=200, null=True, verbose_name=b'Branch label')),
                ('on_master', models.BooleanField(default=False, verbose_name=b'on master')),
                ('commit_message', models.CharField(max_length=200, null=True, verbose_name=b'commit message')),
                ('author', models.CharField(max_length=100, null=True, verbose_name=b'author')),
                ('status_url', models.URLField(null=True, verbose_name=b'status URL')),
                ('display_url', models.URLField(null=True, verbose_name=b'display URL')),
                ('fetch_cmd', models.CharField(max_length=200, null=True, verbose_name=b'fetch command')),
                ('fetch_branch', models.CharField(max_length=200, null=True, verbose_name=b'fetch branch name')),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('finished', models.DateTimeField()),
                ('modified', models.DateTimeField(auto_now=True)),
                ('container', models.CharField(max_length=100, null=True, verbose_name=b'container ID')),
                ('temp_dir', models.CharField(max_length=100, null=True, verbose_name=b'temporary directory')),
                ('pre_log', models.TextField(null=True, verbose_name=b'pre build log')),
                ('main_log', models.TextField(null=True, verbose_name=b'main build log')),
                ('complete', models.BooleanField(default=False, verbose_name=b'processing complete')),
                ('test_success', models.BooleanField(default=True, verbose_name=b'test succeeded')),
                ('test_passed', models.BooleanField(default=False, verbose_name=b'test passed')),
                ('coverage', models.DecimalField(null=True, max_digits=5, decimal_places=2)),
                ('archive', models.FileField(null=True, upload_to=cidonkey.models.archive_dir)),
                ('project', models.ForeignKey(related_name=b'builds', to='cidonkey.Project')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='build',
            name='project',
        ),
        migrations.DeleteModel(
            name='Build',
        ),
        migrations.AddField(
            model_name='project',
            name='docker_image',
            field=models.CharField(default=b'cidonkey', help_text=b'Name of the docker image to use for CI.', max_length=100, verbose_name=b'docker image'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='status_svg',
            field=models.CharField(default=b'null.svg', verbose_name=b'status SVG', max_length=20, editable=False, choices=[(b'null.svg', b'null.svg'), (b'in_progress.svg', b'in_progress.svg'), (b'failing.svg', b'failing.svg'), (b'passing.svg', b'passing.svg')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='project',
            name='ci_url',
            field=models.URLField(help_text=b'URL of this site, used for "datails" on commit statuses.', verbose_name=b'CI URL'),
        ),
    ]
