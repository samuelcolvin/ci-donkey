import subprocess
import shlex
from time import sleep
import datetime
import shutil
import re
from django.conf import settings
from django.core.files import File
from django.utils import timezone
import thread
import traceback
import tempfile
import pytz
import requests
import os
import zipfile

from cidonkey.models import BuildInfo

from . import cidocker, github, common
from settings import MAX_CONCURRENT_BUILDS


def build(bi):
    thread.start_new_thread(BuildProcess.start_build, (bi,))


def check(bi):
    return BuildProcess.check_docker(bi)


class BuildProcess(object):
    def __init__(self, build_info):
        assert isinstance(build_info, BuildInfo), 'build_info must be an instance of BuildInfo, not %s' % \
                                                  build_info.__class__.__name__
        self.build_info = build_info
        self.project = build_info.project
        self.token = self.project.github_token
        self.valid_token = isinstance(self.token, basestring) and len(self.token) > 0
        self.badge_updates = self.build_info.on_master

    @classmethod
    def start_build(cls, build_info):
        """
        run the build script.
        """
        self = BuildProcess(build_info)
        try:
            self.build_info.start = datetime.datetime.now().replace(tzinfo=pytz.UTC)
            self.build_info.process_log = ''
            self._delete_old_containers()
            self.build_info.temp_dir = tempfile.mkdtemp(prefix='cid_src_tmp')
            self._set_url()
            self._log('doing badge updates: %r' % self.badge_updates)
            self.build_info.save()
            self._update_status('pending', 'CI build underway')
            self._set_svg('in_progress')
            self.build_info.save()
            self._download()
            self.build_info.save()
            self._zip_save_repo()
            self.build_info.save()
            self._log('STARTING DOCKER:')
            self.build_info.container = cidocker.start_ci(self.project.docker_image, self.build_info.temp_dir)
            self.build_info.container_exists = True
            self.build_info.save()
            while True:
                sleep(settings.THREAD_CHECK_RATE)
                bi = self._check_docker()
                if bi.complete:
                    break
        except (common.KnownError, common.CommandError), e:
            self._log('%s: %s' % (e.__class__.__name__, str(e)), '')
            self._process_error()
        except Exception:
            self._log(traceback.format_exc())
            self._process_error()
        finally:
            self.build_info.save()
        return self.build_info

    @classmethod
    def check_docker(cls, build_info):
        """
        check status of a build to see if it's finished.
        """
        self = BuildProcess(build_info)
        bi = self._check_docker()
        self._check_queue()
        return bi

    def _check_docker(self):
        if self.build_info.complete:
            return self.build_info
        try:
            if not self.build_info.container_exists:
                return self.build_info
            status = cidocker.check_progress(self.build_info.container)
            if not status:
                return self.build_info
            exit_code, finished, logs, con_inspection = status
            self.build_info.test_success = self.build_info.project.script_split in logs
            if self.build_info.test_success:
                self.build_info.test_passed = exit_code == 0
                process_log, ci_log = logs.split(self.build_info.project.script_split, 1)
                self.build_info.process_log += '\n' + process_log
                self.build_info.ci_log = ci_log
                self.build_info.container_inspection = con_inspection
                if self.project.coverage_regex:
                    m = re.search(self.project.coverage_regex, self.build_info.ci_log)
                    if m:
                        try:
                            self.build_info.coverage = float(m.groups()[0])
                        except (ValueError, IndexError):
                            pass
            else:
                self.build_info.process_log += '\n' + logs
            self._log('DOCKER FINISHED:')
            shutil.rmtree(self.build_info.temp_dir, ignore_errors=True)
            self.build_info.complete = True
            self.build_info.finished = finished

            if self.build_info.test_passed:
                msg = 'CI Success'
                if isinstance(self.build_info.coverage, float):
                    msg += ', %0.2f%% coverage' % self.build_info.coverage
                self._update_status('success', msg)
            else:
                self._update_status('failure', 'Tests failed')
            self._set_svg(self.build_info.test_passed)
        except common.KnownError, e:
            raise e
        except Exception:
            self._log(traceback.format_exc())
            self._process_error()
        finally:
            self.build_info.save()
        return self.build_info

    def _delete_old_containers(self):
        delay = settings.CONTAINER_DELETE_MINUTES
        if delay < 0:
            self._log('Not deleting old containers.')
            return
        n = datetime.datetime.now().replace(tzinfo=pytz.UTC) - datetime.timedelta(minutes=delay)
        del_con_ids = BuildInfo.objects.filter(finished__lt=n).values_list('container', flat=True)
        deleted_cons = cidocker.delete_old_containers(del_con_ids)
        BuildInfo.objects.filter(container__in=deleted_cons).update(container_exists=False)
        self._log('%d old containers deleted.' % len(deleted_cons))

    def _process_error(self):
        self._update_status('error', 'Error running tests')
        self._set_svg(False)
        if self.build_info.temp_dir:
            shutil.rmtree(self.build_info.temp_dir, ignore_errors=True)
        self.build_info.test_success = False
        self.build_info.complete = True
        self.build_info.finished = timezone.now()

    @staticmethod
    def _check_queue():
        """
        Check if a new build can begin, if so start them
        """
        if BuildInfo.objects.filter(complete=False, queued=False).count() < MAX_CONCURRENT_BUILDS:
            queue_first = BuildInfo.objects.filter(queued=True).order_by('id').first()
            if queue_first:
                queue_first.queued = False
                queue_first.save()
                build(queue_first)

    def _set_url(self):
        """
        generate the url which will be used to clone the repo.
        """
        token = ''
        if self.project.private and self.valid_token:
            token = self.token + '@'
        self.url = 'https://%sgithub.com/%s/%s.git' % (token, self.project.github_user, self.project.github_repo)
        self._log('clone url: %s' % self.url)

    def _update_status(self, status, message):
        assert status in ['pending', 'success', 'error', 'failure']
        if not self.build_info.status_url or not settings.SET_STATUS:
            return
        if not self.valid_token:
            self._log('WARNING: no valid token found, cannot update status of pull request')
            return
        payload = {
            'state': status,
            'description': message,
            'context': common.UPDATE_CONTEXT,
            'target_url': self.build_info.project.update_url + str(self.build_info.id)
        }
        _, r = github.github_api(
            url=self.build_info.status_url,
            token=self.token,
            method=requests.post,
            data=payload,
            extra_headers={'Content-type': 'application/json'})
        self._log('updated pull request, status "%s", response: %d' % (status, r.status_code))
        if r.status_code != 201:
            self._log('received unexpected status code, response code')
            self._log('response headers: %r' % r.headers)
            self._log('url posted to: %s' % self.build_info.status_url)
            self._log('payload: %r' % payload)
            self._log('text: %r' % r.text[:1000])

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

    def _zip_save_repo(self):
        self._log('zipping repo...')
        count = 0
        with tempfile.TemporaryFile(suffix='.zip') as temp_file:
            with zipfile.ZipFile(temp_file, 'w') as ztemp_file:
                for root, dirs, files in os.walk(self.build_info.temp_dir):
                    for f in files:
                        full_path = os.path.join(root, f)
                        local_path = full_path.replace(self.build_info.temp_dir, '').lstrip('/')
                        ztemp_file.write(full_path, local_path)
                        count += 1
            self._log('zipped %d files to archive, saving zip file...' % count)
            self.build_info.archive.save(temp_file.name, File(temp_file))

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
                cienv = {}# os.environ.copy()
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
        self.project.save()

    def _message(self, message):
        if not message.endswith('\n'):
            message += '\n'
        self.build_info.process_log += message

    def _log(self, line, prefix='#> '):
        self._message(prefix + line.strip('\n\r \t'))


