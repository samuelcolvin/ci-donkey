# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cidonkey.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BuildInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sha', models.CharField(max_length=50, null=True, verbose_name=b'commit sha', blank=True)),
                ('trigger', models.CharField(max_length=20, verbose_name=b'trigger')),
                ('action', models.CharField(max_length=20, null=True, verbose_name=b'action', blank=True)),
                ('label', models.CharField(max_length=200, null=True, verbose_name=b'branch label', blank=True)),
                ('on_master', models.BooleanField(default=False, verbose_name=b'on master')),
                ('commit_message', models.CharField(max_length=200, null=True, verbose_name=b'commit message', blank=True)),
                ('author', models.CharField(max_length=100, null=True, verbose_name=b'author', blank=True)),
                ('status_url', models.URLField(null=True, verbose_name=b'status URL', blank=True)),
                ('display_url', models.URLField(null=True, verbose_name=b'display URL', blank=True)),
                ('fetch_cmd', models.CharField(max_length=200, null=True, verbose_name=b'fetch command', blank=True)),
                ('fetch_branch', models.CharField(max_length=200, null=True, verbose_name=b'fetch branch name', blank=True)),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('finished', models.DateTimeField(null=True, blank=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'last modified')),
                ('container', models.CharField(max_length=100, null=True, verbose_name=b'container ID', blank=True)),
                ('temp_dir', models.CharField(max_length=100, null=True, verbose_name=b'temporary directory', blank=True)),
                ('process_log', models.TextField(null=True, verbose_name=b'process log', blank=True)),
                ('ci_log', models.TextField(null=True, verbose_name=b'ci log', blank=True)),
                ('pre_log', models.TextField(null=True, verbose_name=b'pre build log', blank=True)),
                ('main_log', models.TextField(null=True, verbose_name=b'main build log', blank=True)),
                ('docker_started', models.BooleanField(default=False, verbose_name=b'docker started')),
                ('complete', models.BooleanField(default=False, verbose_name=b'complete')),
                ('test_success', models.BooleanField(default=True, verbose_name=b'test succeeded')),
                ('test_passed', models.BooleanField(default=False, verbose_name=b'test passed')),
                ('coverage', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
                ('archive', models.FileField(null=True, upload_to=cidonkey.models.archive_dir, blank=True)),
            ],
            options={
                'ordering': ['-id'],
                'verbose_name': 'Build',
                'verbose_name_plural': 'Builds',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('github_user', models.CharField(help_text=b'github user or organisation name', max_length=100, verbose_name=b'github username')),
                ('github_repo', models.CharField(help_text=b'github repo name', max_length=100, verbose_name=b'github repo')),
                ('github_token', models.CharField(help_text=b'The token needs the "repo" scope to clone private repos. Used for cloning on private repos and for updating pull request statuses on all repos.', max_length=50, verbose_name=b'github token')),
                ('private', models.BooleanField(default=True)),
                ('webhooks', models.CharField(default=b'push, pull_request', help_text=b'Comma separated list of wehbooks to accept from github, see here for details.Normally push and pull_request will suffice.', max_length=100)),
                ('ci_script', models.CharField(default=b'ci-donkey.sh', help_text=b'path inside repo to script which is executed to perform CI.', max_length=200, verbose_name=b'CI script path')),
                ('script_split', models.CharField(default=b'**MAIN SCRIPT**', help_text=b'tag splitting the pre script and main script, this should be written to stdout to start the main script.', max_length=100, verbose_name=b'script splitter')),
                ('docker_image', models.CharField(default=b'cidonkey', help_text=b'Name of the docker image to use for CI.', max_length=100, verbose_name=b'docker image')),
                ('default_branch', models.CharField(default=b'master', max_length=50, verbose_name=b'default branch')),
                ('allow_repeat', models.BooleanField(default=False, help_text=b'Allow repeat builds for the same sha.', verbose_name=b'allow_repeats')),
                ('webhook_secret', models.CharField(max_length=100, verbose_name=b'webhook secret', blank=True)),
                ('status_svg', models.CharField(default=b'null.svg', max_length=20, verbose_name=b'status SVG', blank=True, choices=[(b'null.svg', b'null.svg'), (b'in_progress.svg', b'in_progress.svg'), (b'failing.svg', b'failing.svg'), (b'passing.svg', b'passing.svg')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='buildinfo',
            name='project',
            field=models.ForeignKey(related_name=b'builds', to='cidonkey.Project'),
            preserve_default=True,
        ),
    ]
