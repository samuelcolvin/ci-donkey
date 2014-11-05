import uuid
import datetime
import random
import string
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe


def random_string(length=50):
    rand = lambda: random.choice(string.lowercase + string.uppercase + string.digits)
    return ''.join(rand() for _ in range(length))


class Project(models.Model):
    github_user = models.CharField('github username', max_length=100, help_text='github user or organisation name')
    github_repo = models.CharField('github repo', max_length=100, help_text='github repo name')
    github_token = models.CharField('github token', max_length=50,
                                    help_text='The token needs the "repo" scope to clone private repos. Used '
                                              'for cloning on private repos and for updating pull '
                                              'request statuses on all repos.')
    private = models.BooleanField(default=True)
    webhooks = models.CharField(max_length=100, default='push, pull_request',
                                help_text='Comma separated list of wehbooks to accept from github, see here '
                                          'for details.Normally push and pull_request will suffice.')
    ci_script = models.CharField('CI script path', max_length=200, default='ci-donkey.sh',
                                 help_text='path inside repo to script which is executed to perform CI.')
    script_split = models.CharField('script splitter', max_length=100, default='**MAIN SCRIPT**',
                                    help_text='tag splitting the pre script and main script, this should '
                                              'be written to stdout to start the main script.')
    coverage_regex = models.CharField('coverage regex', max_length=500, null=True, blank=True,
                                      default='\nOVERALL COVERAGE = ([\d\.]+)%\n',
                                      help_text='regular expression to use to search for overage value, should have '
                                                'one group with can be parsed as a float.')
    docker_image = models.CharField('docker image', max_length=100, default='cidonkey',
                                    help_text='Name of the docker image to use for CI.')
    default_branch = models.CharField('default branch', default='master', max_length=50)
    allow_repeat = models.BooleanField('allow_repeats', default=False,
                                       help_text='Allow repeat builds for the same sha.')
    # TODO: this should be set to editable=False
    webhook_secret = models.CharField(max_length=100, editable=False)
    update_url = models.CharField(max_length=200, default='unknown', editable=False)

    SVG_NULL = 'null.svg'
    SVG_IN_PROGRESS = 'in_progress.svg'
    SVG_FAILING = 'failing.svg'
    SVG_PASSING = 'passing.svg'
    SVG_STATUSES = [(f, f) for f in (SVG_NULL, SVG_IN_PROGRESS, SVG_FAILING, SVG_PASSING)]
    status_svg = models.CharField('status SVG', choices=SVG_STATUSES, default=SVG_NULL, blank=True, max_length=20)

    def __unicode__(self):
        return '%s/%s' % (self.github_user, self.github_repo)

    def save(self, **kwargs):
        if not self.webhook_secret:
            self.webhook_secret = random_string()
        return super(Project, self).save(**kwargs)


def archive_dir(instance, filename):
    name = instance.sha if instance.sha else str(uuid.uuid4())
    n = datetime.datetime.now()
    stamp = n.strftime('%d-%b-%Y,%a_%H-%M-%S')
    folder = n.strftime('%Y_%m')
    return '%s/%s_%s.zip' % (folder, stamp, name)


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

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField('last modified', auto_now=True)
    start = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)

    container = models.CharField('container ID', max_length=100, null=True, blank=True)
    container_exists = models.BooleanField('container exists', default=False)
    container_inspection = models.TextField('container inspection', null=True, blank=True)
    temp_dir = models.CharField('temporary directory', max_length=100, null=True, blank=True)

    process_log = models.TextField('process log', null=True, blank=True)
    ci_log = models.TextField('ci log', null=True, blank=True)
    complete = models.BooleanField('complete', default=False)
    test_success = models.BooleanField('test succeeded', default=True)
    test_passed = models.BooleanField('test passed', default=False)
    queued = models.BooleanField('queued', default=False)

    coverage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    archive = models.FileField(upload_to=archive_dir, null=True, blank=True)

    def successful(self):
        if self.queued:
            return 'glyphicon-pause'
        if not self.complete:
            return 'glyphicon-play'
        if not self.test_success:
            return 'FAIL'
        return self.test_passed
    successful.short_description = 'successful'

    def time_taken(self):
        if self.queued:
            return '-'
        if not self.complete:
            return self.start
        if not self.finished:
            return ''
        diff = self.finished - self.start
        total_seconds = diff.total_seconds()

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
                # should not show fractions for 1min 1 sec
                fmt = '%02.0fs' if total_seconds > 2 else '%05.02fs'
                return fmt % f

        return float2time(total_seconds)
    time_taken.short_description = 'time taken'

    def show_coverage(self):
        if self.coverage is None:
            return ''
        return ('%0.2f' % self.coverage).rstrip('.0') + '%'
    show_coverage.short_description = 'coverage'

    def commit_url(self):
        if not self.commit_message:
            return ''
        if not self.display_url:
            return self.commit_message
        return mark_safe('<a href="%s">%s</a>' % (self.display_url, self.commit_message))
    commit_url.short_description = 'commit'

    def __unicode__(self):
        return self.sha or 'unknown'

    class Meta:
        ordering = ['-id']
        verbose_name = 'Build'
        verbose_name_plural = 'Builds'
