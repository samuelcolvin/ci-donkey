import subprocess
import shlex
from cidonkey.models import BuildInfo
import os
import re
import thread
import traceback
import tempfile
import requests
import datetime
from . import cidocker, github, common


def build(bi):
    b = BuildProcess(bi)
    thread.start_new_thread(b.start_build, ())


def check(bi):
    b = BuildProcess(bi)
    return b.check_docker()


class BuildProcess(object):
    def __init__(self, build_info):
        assert isinstance(build_info, BuildInfo), 'build_info must be an instance of BuildInfo, not %s' % \
                                                  build_info.__class__.__name__
        self.build_info = build_info
        self.project = build_info.project
        self.token = self.project.github_token
        self.valid_token = isinstance(self.token, basestring) and len(self.token) > 0
        self.badge_updates = False
        changed = False
        if self.build_info.temp_dir is None:
            self.build_info.temp_dir = tempfile.mkdtemp()
            changed = True
        if self.build_info.pre_log is None:
            self.build_info.pre_log = ''
            changed = True
        if changed:
            self.build_info.save()

    def start_build(self):
        """
        run the build script.
        """
        try:
            self._set_url()
            self.badge_updates = self.build_info.on_master
            self._log('doing badge updates: %r' % self.badge_updates)
            self._update_status('pending', 'CI build underway')
            self._set_svg('in_progress')
            self._download()
            self.build_info.container = cidocker.start_ci(self.project.docker_image, self.build_info.temp_dir)
        except (common.KnownError, common.CommandError), e:
            self._log('%s: %s' % (e.__class__.__name__, str(e)), '')
            self._process_error()
        except Exception:
            self._log(traceback.format_exc())
            self._process_error()
        finally:
            self.build_info.save()
        return self.build_info

    def check_docker(self):
        if self.build_info.complete:
            return self.build_info
        try:
            status = cidocker.check_progress(self.build_info.container)
            if not status:
                return self.build_info
            exit_code, finished, logs = status
            self.build_info.test_passed = exit_code == 0
            self.build_info.main_log = logs
            self.build_info.complete = True
            self.build_info.finished = finished

            if self.build_info.test_passed:
                self._update_status('success', 'CI Success')
            else:
                self._update_status('failure', 'Tests failed')
            self._set_svg(self.build_info.test_passed)
        except Exception, e:
            self._log(traceback.format_exc())
            self._process_error()
        finally:
            self.build_info.save()
        return self.build_info

    def _process_error(self):
        self._update_status('error', 'Error running tests')
        self._set_svg(False)
        self.build_info.test_success = False
        self.build_info.complete = True
        self.build_info.finished = datetime.datetime.now()

    def _set_url(self):
        """
        generate the url which will be used to clone the repo.
        """
        self.url = self.project.github_url
        if self.project.private and self.valid_token:
            self.url = re.sub('https://', 'https://%s@' % self.token, self.url)
        self._log('clone url: %s' % self.url)

    def _update_status(self, status, message):
        assert status in ['pending', 'success', 'error', 'failure']
        if not self.build_info.status_url:
            return
        if not self.valid_token:
            self._log('WARNING: no valid token found, cannot update status of pull request')
            return
        target_url = self.project.ci_url + 'xyz'# + reverse('view-build', kwargs={'pk':self.build_info.id)
        payload = {
            'state': status,
            'description': message,
            'context': 'ci-donkey',
            'target_url': target_url
        }
        _, r = github.api(
            url=self.build_info.status_url,
            token=self.token,
            method=requests.post,
            data=payload)
        self._log('updated pull request, status "%s", response: %d' % (status, r.status_code))
        if r.status_code != 201:
            self._log('received unexpected status code, response text:')
            self._log('url posted to: %s' % self.build_info.status_url)
            self._log(r.text[:1000])

    def _download(self):
        self._log('cloning...')
        commands = 'git clone %s %s' % (self.url, self.build_info.temp_dir)
        self._execute(commands)
        self._log('cloned code successfully')
        if self.build_info.fetch_cmd:
            self._log('fetching branch ' + self.build_info.fetch_cmd)
            commands = ['git fetch origin ' + self.build_info.fetch_cmd]
            if self.build_info.fetch_branch:
                commands.append('git checkout ' + self.build_info.fetch_branch)
            self._execute(commands)
        if self.build_info.sha:
            self._log('checkout out ' + self.build_info.sha)
            self._execute('git checkout ' + self.build_info.sha)

    def _execute(self, commands):
        if isinstance(commands, basestring):
            commands = [commands]
        for command in commands:
            if command.strip().startswith('#'):
                self._log(command, 'SKIP> ')
                continue
            self._log(command, 'EXEC> ')
            cargs = shlex.split(command)
            try:
                cienv = os.environ.copy()
                cienv['CIDONKEY'] = '1'
                p = subprocess.Popen(cargs,
                                     cwd=self.build_info.temp_dir,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     env=cienv)
                stdout, stderr = p.communicate()
                if len(stdout) > 0:
                    self._log(stdout, '')
                if p.returncode != 0:
                    raise common.CommandError(stderr)
                elif len(stderr) > 0:
                    self._log(stderr)
            except common.CommandError, e:
                raise e
            except Exception, e:
                raise common.KnownError('%s: %s' % (e.__class__.__name__, str(e)))

    def _set_svg(self, status):
        if not self.badge_updates:
            return
        if status == 'in_progress':
            status_svg = 'in_progress.svg'
        else:
            status_svg = 'passing.svg' if status else 'failing.svg'
        self._log('setting status svg to %s' % status_svg)
        self.project.status_svg = status_svg

    def _message(self, message):
        if not message.endswith('\n'):
            message += '\n'
        self.build_info.pre_log += message

    def _log(self, line, prefix='#> '):
        self._message(prefix + line.strip('\n\r \t'))


