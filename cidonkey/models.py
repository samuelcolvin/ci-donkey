from django.db import models


class Project(models.Model):
    name = models.CharField('name', max_length=100, unique=True)
    github_token = models.CharField('github token', max_length=50,
                                    help_text='The token needs the "repo" scope to clone private repos. Used'
                                              ' for cloning on private repos and for updating pull '
                                              'request statuses on all repos.')
    private = models.BooleanField(default=True)
    github_url = models.URLField('github URL', null=True, help_text='This should be the https url for github.')
    ci_url = models.URLField('CI URL', null=True, help_text='URL of this site, used for "datails" on commit statuses.')
    webhooks = models.CharField(max_length=100, default='push, pull_request',
                                help_text='Comma seperated list of webooks to accept from github, see here '
                                          'for details.Normally push and pull_request will suffice.')
    ci_script = models.CharField('CI script path', max_length=200, default='ci-donkey.sh',
                                 help_text='path inside repo to script which is executed to perform CI.')
    script_split = models.CharField('script splitter', max_length=100, default='**MAIN SCRIPT**',
                                    help_text='tag splitting the pre script and main script, this should '
                                              'be written to stdout to start the main script.')

    def __unicode__(self):
        return self.name


def archive_dir(instance, filename):
    return '%s.zip' % instance.sha


class Build(models.Model):
    project = models.ForeignKey(Project, related_name='builds')

    sha = models.CharField('commit sha', max_length=50)
    trigger = models.CharField('trigger', max_length=20, null=True)
    action = models.CharField('action', max_length=20, null=True)
    label = models.CharField('Branch label', max_length=200, null=True)
    on_master = models.BooleanField('on master', default=False)
    commit_message = models.CharField('commit message', max_length=200, null=True)
    author = models.CharField('author', max_length=100, null=True)
    status_url = models.URLField('status URL', null=True)
    display_url = models.URLField('display URL', null=True)

    fetch_cmd = models.CharField('fetch command', max_length=200, null=True)
    fetch_branch = models.CharField('fetch branch name', max_length=200, null=True)

    start = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField()
    modified = models.DateTimeField(auto_now=True)

    pre_log = models.TextField('pre build log', null=True)
    main_log = models.TextField('main build log', null=True)
    complete = models.BooleanField('processign complete', default=False)
    test_success = models.BooleanField('test succeeded', default=False)
    test_passed = models.BooleanField('test passed', default=False)
    coverage = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    archive = models.FileField(upload_to=archive_dir, null=True)

    def time_taken(self):
        def float2time(f):
            if f is None:
                return ''
            elif f >= 3600:
                h = int(f / 3600)
                return '%2d:%s' % (h, float2time(f % 3600))
            elif f >= 60:
                m = int(f / 60)
                return '%02d:%s' % (m, float2time(f % 60))
            else:
                fmt = '%05.02f'
                if round(f) == f:
                    fmt = '%02.0fs'
                return fmt % f
        diff = self.finished - self.start
        return float2time(diff.total_seconds())
    time_taken.short_description = 'time taken'

    def __unicode__(self):
        return self.sha or 'unknown'
