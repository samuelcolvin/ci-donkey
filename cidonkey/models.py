from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe


class Project(models.Model):
    name = models.CharField('name', max_length=100, unique=True)
    github_token = models.CharField('github token', max_length=50,
                                    help_text='The token needs the "repo" scope to clone private repos. Used '
                                              'for cloning on private repos and for updating pull '
                                              'request statuses on all repos.')
    private = models.BooleanField(default=True)
    github_url = models.URLField('github URL', null=True, help_text='This should be the https url for github.')
    ci_url = models.URLField('CI URL', help_text='URL of this site, used for "datails" on commit statuses.')
    webhooks = models.CharField(max_length=100, default='push, pull_request',
                                help_text='Comma seperated list of webooks to accept from github, see here '
                                          'for details.Normally push and pull_request will suffice.')
    ci_script = models.CharField('CI script path', max_length=200, default='ci-donkey.sh',
                                 help_text='path inside repo to script which is executed to perform CI.')
    script_split = models.CharField('script splitter', max_length=100, default='**MAIN SCRIPT**',
                                    help_text='tag splitting the pre script and main script, this should '
                                              'be written to stdout to start the main script.')
    docker_image = models.CharField('docker image', max_length=100, default='cidonkey',
                                    help_text='Name of the docker image to use for CI.')

    SVG_NULL = 'null.svg'
    SVG_IN_PROGRESS = 'in_progress.svg'
    SVG_FAILING = 'failing.svg'
    SVG_PASSING = 'passing.svg'
    SVG_STATUSES = [(f, f) for f in (SVG_NULL, SVG_IN_PROGRESS, SVG_FAILING, SVG_PASSING)]
    status_svg = models.CharField('status SVG', choices=SVG_STATUSES, default=SVG_NULL, editable=False, max_length=20)

    def __unicode__(self):
        return self.name


def archive_dir(instance, filename):
    return '%s.zip' % instance.sha


class BuildInfo(models.Model):
    project = models.ForeignKey(Project, related_name='builds')

    sha = models.CharField('commit sha', max_length=50, null=True, blank=True)
    trigger = models.CharField('trigger', max_length=20)
    action = models.CharField('action', max_length=20, null=True, blank=True)
    label = models.CharField('branch label', max_length=200, null=True, blank=True)
    on_master = models.BooleanField('on master', default=False)
    commit_message = models.CharField('commit message', max_length=200, null=True, blank=True)
    author = models.CharField('author', max_length=100, null=True, blank=True)
    status_url = models.URLField('status URL', null=True, blank=True)
    display_url = models.URLField('display URL', null=True, blank=True)

    fetch_cmd = models.CharField('fetch command', max_length=200, null=True, blank=True)
    fetch_branch = models.CharField('fetch branch name', max_length=200, null=True, blank=True)

    start = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True, blank=True)
    modified = models.DateTimeField('last modified', auto_now=True)

    container = models.CharField('container ID', max_length=100, null=True, blank=True)
    temp_dir = models.CharField('temporary directory', max_length=100, null=True, blank=True)

    pre_log = models.TextField('pre build log', null=True, blank=True)
    main_log = models.TextField('main build log', null=True, blank=True)
    docker_started = models.BooleanField('docker started', default=False)
    complete = models.BooleanField('complete', default=False)
    test_success = models.BooleanField('test succeeded', default=True)
    test_passed = models.BooleanField('test passed', default=False)
    coverage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    archive = models.FileField(upload_to=archive_dir, null=True, blank=True)

    def successful(self):
        if not self.complete:
            return 'glyphicon-play'
        return self.test_success and self.test_passed
    successful.short_description = 'successful'

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
                fmt = '%0.0fs' if f > 2 else '%0.2fs'
                return fmt % f
        fin = self.finished if self.complete else timezone.now()
        if not fin:
            return ''
        diff = fin - self.start
        return float2time(diff.total_seconds())
    time_taken.short_description = 'time taken'

    def commit_url(self):
        return mark_safe('<a href="%s">%s</a>' % (self.display_url, self.commit_message))
    commit_url.short_description = 'commit'

    def __unicode__(self):
        return self.sha or 'unknown'

    class Meta:
        ordering = ['-id']
        verbose_name = 'Build'
        verbose_name_plural = 'Builds'
