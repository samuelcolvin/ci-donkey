# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cidonkey.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Build',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sha', models.CharField(max_length=50, verbose_name=b'commit sha')),
                ('trigger', models.CharField(max_length=20, null=True, verbose_name=b'trigger')),
                ('action', models.CharField(max_length=20, null=True, verbose_name=b'action')),
                ('label', models.CharField(max_length=200, null=True, verbose_name=b'Branch label')),
                ('on_master', models.BooleanField(default=False, verbose_name=b'on master')),
                ('commit_message', models.CharField(max_length=200, null=True, verbose_name=b'commit message')),
                ('author', models.CharField(max_length=100, null=True, verbose_name=b'author')),
                ('status_url', models.URLField(null=True, verbose_name=b'status URL')),
                ('display_url', models.URLField(null=True, verbose_name=b'display URL')),
                ('fetch_cmd', models.CharField(max_length=200, null=True, verbose_name=b'fetch command')),
                ('fetch_branch', models.CharField(max_length=200, null=True, verbose_name=b'fetch branch name')),
                ('start', models.DateField(auto_now_add=True)),
                ('finished', models.DateField()),
                ('modified', models.DateField(auto_now=True)),
                ('pre_log', models.TextField(null=True, verbose_name=b'pre build log')),
                ('main_log', models.TextField(null=True, verbose_name=b'main build log')),
                ('complete', models.BooleanField(default=False, verbose_name=b'processign complete')),
                ('test_success', models.BooleanField(default=False, verbose_name=b'test succeeded')),
                ('test_passed', models.BooleanField(default=False, verbose_name=b'test passed')),
                ('coverage', models.DecimalField(null=True, max_digits=5, decimal_places=2)),
                ('archive', models.FileField(null=True, upload_to=cidonkey.models.archive_dir)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name=b'name')),
                ('github_token', models.CharField(help_text=b'The token needs the "repo" scope to clone private repos. Used for cloning on private repos and for updating pull request statuses on all repos.', max_length=50, verbose_name=b'github token')),
                ('private', models.BooleanField(default=True)),
                ('github_url', models.URLField(help_text=b'This should be the https url for github.', null=True, verbose_name=b'github URL')),
                ('ci_url', models.URLField(help_text=b'URL of this site, used for "datails" on commit statuses.', null=True, verbose_name=b'CI URL')),
                ('webhooks', models.CharField(default=b'push, pull_request', help_text=b'Comma seperated list of webooks to accept from github, see here for details.Normally push and pull_request will suffice.', max_length=100)),
                ('ci_script', models.CharField(default=b'ci-donkey.sh', help_text=b'path inside repo to script which is executed to perform CI.', max_length=200, verbose_name=b'CI script path')),
                ('script_split', models.CharField(default=b'**MAIN SCRIPT**', help_text=b'tag splitting the pre script and main script, this should be written to stdout to start the main script.', max_length=100, verbose_name=b'script splitter')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='build',
            name='project',
            field=models.ForeignKey(related_name=b'builds', to='cidonkey.Project'),
            preserve_default=True,
        ),
    ]
