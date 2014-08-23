from datetime import datetime as dtdt
from . import app
import subprocess
import shlex
import git
import os
import json
import re
import thread
import traceback
import shutil
import time
import tempfile
import requests

def dt_from_str(dstr_in):
    # remove %s encoding of unix time stamp
    dstr = re.sub('\d\d\d\d\d\d*', '', dstr_in)
    fmat = app.config['DATETIME_FORMAT'].replace('%s', '')
    try:
        return dtdt.strptime(dstr, fmat)
    except ValueError:
        return dtdt(1970,1,1)

def setup_cls():
    if os.path.exists(app.config['SETUP_FILE']):
        obj = json.load(open(app.config['SETUP_FILE'], 'r'))
        obj['datetime'] = dt_from_str(obj['datetime'])
        return type('CISetup', (), obj)

def build(build_info):
    b = Build(build_info)
    thread.start_new_thread(b.build, ())
    return b.stamp

def _now():
    return dtdt.utcnow().strftime(app.config['DATETIME_FORMAT'])

def _build_log_path(id):
    return os.path.join('/tmp', id + '.log')

class KnownError(Exception):
    pass

class CommandError(Exception):
    pass

TERMINAL_ERROR =   '#############   TERMINAL ERROR   #############\n'
TEST_ERROR =       '#############     TEST ERROR     #############\n'
LOG_PRE_FINISHED = '############# PRE BUILD FINISHED #############\n'
LOG_FINISHED =     '#############      FINISHED      #############\n'
CLEANED_UP =       '#############     CLEANED UP     #############\n'
END_OF_BS =        '==============================================\n'

class Build(object):
    def __init__(self, build_info):
        self.setup = setup_cls()
        self.token = self.setup.github_token
        self.valid_token = isinstance(self.token, basestring) and len(self.token) > 0
        self.stamp = _now()# str(uuid.uuid4())
        self.delete_after = not self.setup.save_repo
        self.log_file = _build_log_path(self.stamp)
        self.build_info = dict(build_info)
        self._message(json.dumps(build_info, indent=2))
        self._message(END_OF_BS)
        self._log('Starting build at %s' % _now())
        self._log('log filename: %s' % self.log_file)
        save_dir = self.setup.save_dir if self.setup.save_dir else tempfile.gettempdir()
        self.repo_path = os.path.join(save_dir, self.stamp)
        self._log('project directory: %s' % self.repo_path)
        self.pre_script = []
        self.main_script = []
        self.badge_updates = False

    def build(self):
        """
        run the build script.
        """
        try:
            if not self.prebuild(): return
            if not self.main_build(): return
        except Exception, e:
            raise e
        finally:
            self._finish()

    def prebuild(self):
        try:
            # first we save a blank log item so it's in history
            logs = history()
            logs.append(log_info(self.stamp))
            self._save_logs(logs)

            self._set_url()
            self.badge_updates = self._decide_badge_updates()
            self._update_status('pending', 'CI build underway')
            self._set_svg('in_progress')
            self._download()
            self._get_ci_script()
            self._execute(self.pre_script)
        except Exception, e:
            self._error(e)
            return False
        else:
            self._message(LOG_PRE_FINISHED)
            return True

    def main_build(self):
        try:
            self._execute(self.main_script)
        except Exception, e:
            self._error(e, True)
            return False
        else:
            self._message(LOG_FINISHED)
            return True

    def _set_url(self):
        """
        generate the url which will be used to clone the repo.
        """
        self.url = self.build_info.get('git_url', None)
        if self.url is None:
            self.url = self.setup.git_url
        private = self.build_info.get('private', True)
        if private and self.valid_token:
            if self.url.startswith('git://'):
                self.url = self.url.replace('git://', 'https://')
            self.url = re.sub('https://', 
                'https://%s@' % self.token, self.url)
            self._log('clone url: %s' % self.url.replace(self.token, '<token>'))
        else:
            self._log('clone url: %s' % self.url)

    def _decide_badge_updates(self):
        """
        decide whether we are on the default branch on the main repo,
        if so the badge will get updated, otherwise not.
        """
        route = lambda url: url[url.index('github.com'):]
        if route(self.url) != route(self.setup.git_url):
            self._log('git url is not the main repo, no badge updates')
            return False
        if 'default_branch' not in self.build_info:
            self._log('master_branch not in build_info, no badge updates')
            return False
        if not self.build_info.get('label', '').endswith(self.build_info['default_branch']):
            self._log('not on default_branch, no badge updates')
            return False
        self._log('detected default branch, badge will be updated')
        return True

    def _update_status(self, status, message):
        assert status in ['pending', 'success', 'error', 'failure']
        if self.build_info.get('trigger', None) != 'pull_request':
            return
        if not self.valid_token:
            self._log('WARNING: no valid token found, cannot update status of pull request')
            return
        try:
            if self.setup.this_url == '':
                raise Exception('this_url is null')
            target_url = os.path.join(self.setup.this_url, 'show_build', self.stamp)
        except Exception, e:
            self._log('error getting target_url for status update: %r' % e)
            target_url = 'https://github.com/samuelcolvin/ci-donkey'
        payload = {'state': status, 
                   'description': message, 
                   'context': 'ci-donkey', 
                   'target_url': target_url
        }
        payload = json.dumps(payload)
        headers = {'Authorization': 'token %s' % self.token}
        url = self.setup.git_url
        gh = 'github.com'
        uri = url[url.index(gh)+len(gh):]
        if uri.endswith('.git'):
            uri = uri[:-4]
        else:
            uri = uri.rstrip('/')

        url = 'https://api.github.com/repos' + uri + '/statuses/%s' % self.build_info['sha']
        r = requests.post(url, data=payload, headers=headers)
        self._log('updated pull request, status "%s", response: %d' % (status, r.status_code))
        if r.status_code != 201:
            self._log('recieved unexpected status code, response text:')
            self._log('url posted to: %s' % url)
            self._log(r.text[:1000])

    def _download(self):
        self._log('cloning...')
        git.Git().clone(self.url, self.repo_path)
        self._log('cloned code successfully')
        if 'sha' in self.build_info:
            self._log('checkout out %s' % self.build_info['sha'])
            repo = git.Repo(self.repo_path)
            repo.git.checkout(self.build_info['sha'])

    def _get_ci_script(self):
        ci_script_name = self.setup.ci_script
        ci_script_path = os.path.join(self.repo_path, ci_script_name)
        if not os.path.exists(ci_script_path):
            raise KnownError('Repo has no CI script file: %s' % ci_script_name)
        ci_script = open(ci_script_path, 'r').read()
        self._log('found CI script: %s' % ci_script_name)
        if self.setup.main_tag not in ci_script:
            raise KnownError('Config has no divider: %s' % self.setup.main_tag)
        current_script = []
        for line in ci_script.split('\n'):
            if self.setup.pre_tag in line or line == '':
                current_script = self.pre_script
                continue
            if self.setup.main_tag in line:
                current_script = self.main_script
                continue
            current_script.append(line)
        obj = (self.pre_script, self.main_script)
        json.dump(obj, open(build_script_path(self.stamp), 'w'), indent = 2)

    def _execute(self, commands):
        for command in commands:
            if command.strip().startswith('#'):
                self._log(command, 'SKIP> ')
                continue
            self._log(command, 'EXEC> ')
            cargs = shlex.split(command)
            try:
                p = subprocess.Popen(cargs, 
                    cwd = self.repo_path, 
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE)
                stdout, stderr = p.communicate()
                self._log(stdout, '')
                if p.returncode != 0:
                    raise CommandError(stderr)
            except CommandError, e:
                raise e
            except Exception, e:
                raise KnownError('%s: %s' % (e.__class__.__name__, str(e)))

    def _error(self, e, errors_expected = False):
        if errors_expected and isinstance(e, CommandError):
            self._log('%s: %s' % (e.__class__.__name__, str(e)), '')
            self._message(TEST_ERROR)
            self._message(LOG_FINISHED)
            return
        if isinstance(e, KnownError) or isinstance(e, CommandError):
            self._log('%s: %s' % (e.__class__.__name__, str(e)), '')
        else:
            tb = traceback.format_exc()
            self._log(tb)
        self._message(TERMINAL_ERROR)

    def _finish(self):
        # make sure log file has finished being written
        self._log('Build finished at %s, cleaning up' % _now())
        if self.delete_after and os.path.exists(self.repo_path):
            self._log('deleting repo dir %s' % self.repo_path)
            shutil.rmtree(self.repo_path, ignore_errors = False)
        else:
            self._log('removing all untracked file from repo...')
            self._execute(['git clean -f -d -X'])
        self._message(CLEANED_UP)
        time.sleep(2)
        logs = [log for log in history() if log['build_id'] != self.stamp]
        linfo = log_info(self.stamp, self.pre_script, self.main_script)
        logs.append(linfo)
        self._save_logs(logs)
        if linfo['test_passed']:
            self._update_status('success', 'CI Success')
        else:
            if linfo['term_error']:
                self._update_status('error', 'Error running tests')
            else:
                self._update_status('failure', 'Tests failed')
        self._set_svg(linfo['test_passed'])
        if self.delete_after:
            os.remove(self.log_file)
            os.remove(build_script_path(self.stamp))

    def _save_logs(self, logs):
        max_len = app.config['MAX_LOG_LENGTH']
        if max_len:
            logs = logs[-max_len:]
        json.dump(logs, open(app.config['LOG_FILE'], 'w'), indent = 2)
        return logs

    def _set_svg(self, status):
        if not self.badge_updates:
            return
        if status == 'in_progress':
            filename = 'in_progress.svg'
        else:
            filename = 'passing.svg' if status else 'failing.svg'
        thisdir = os.path.dirname(__file__)
        src = os.path.join(thisdir, 'static', filename)
        shutil.copyfile(src, app.config['STATUS_SVG_FILE'])

    def _message(self, message):
        with open(self.log_file, 'a') as logfile:
            if message.endswith('\n'):
                logfile.write(message)
            else:
                logfile.write(message + '\n')
            logfile.flush()

    def _log(self, line, prefix = '#> '):
        self._message(prefix + line.strip('\n \t'))


def log_info(build_id, pre_script = None, main_script = None):
    if pre_script == None and main_script == None:
        script_path = build_script_path(build_id)
        if os.path.exists(script_path):
            pre_script, main_script = json.load(open(script_path, 'r'))
    with open(_build_log_path(build_id), 'r') as logfile:
        log = logfile.read()
        status = {'build_id': build_id}
        status['datetime'] = re.search('Starting build at (.*)', log).groups()[0]
        try:
            status.update(json.loads(log[:log.index(END_OF_BS)]))
        except Exception:
            print 'error processing json build info from log %s' % build_id
        prelog = log
        mainlog = None
        prefin = LOG_PRE_FINISHED in log
        if prefin:
            prelog, mainlog = prelog.split(LOG_PRE_FINISHED)
            prelog += LOG_PRE_FINISHED
        term_error = TERMINAL_ERROR in log
        finished = LOG_FINISHED in log or term_error
        processing_complete = CLEANED_UP in log or term_error
        status['test_passed'] = TEST_ERROR not in log and finished and not term_error
        status['prelog'] = prelog
        status['mainlog'] = mainlog
        status['term_error'] = term_error
        status['finished'] = finished
        status['processing_complete'] = processing_complete
        status['pre_script'] = pre_script
        status['main_script'] = main_script
        # import pprint
        # pprint.pprint(status)
        return status

def history():
    logs = []
    if os.path.exists(app.config['LOG_FILE']):
        logs = json.load(open(app.config['LOG_FILE'], 'r'))
    return logs

def build_script_path(id):
    return os.path.join('/tmp', id + '.script')