from datetime import datetime as dtdt
from . import app
import subprocess
import shlex
import git
import uuid
import os
import json
import re
import thread
import traceback
import shutil
import time
import tempfile

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

    def set_url(self):
        self.url = self.build_info.get('git_url', None)
        if self.url is None:
            self.url = self.setup.git_url
        private = self.build_info.get('private', True)
        t = self.setup.github_token
        if private and len(t) > 0:
            self.url = re.sub('https://', 
                'https://%s@' % t, self.url)
            self._log('clone url: %s' % self.url.replace(t, '<token>'))
        else:
            self._log('clone url: %s' % self.url)

    def build(self):
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

            self.set_url()
            self._set_svg('in_progress')
            self.download()
            self.get_ci_script()
            self.execute(self.pre_script)
        except Exception, e:
            self._error(e)
            return False
        else:
            self._message(LOG_PRE_FINISHED)
            return True

    def download(self):
        self._log('cloning...')
        git.Git().clone(self.url, self.repo_path)
        self._log('cloned code successfully')
        if 'sha' in self.build_info:
            print 'checkout out %s' % self.build_info['sha']
            repo = git.Repo(self.repo_path)
            repo.git.checkout(self.build_info['sha'])

    def get_ci_script(self):
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

    def main_build(self):
        try:
            self.execute(self.main_script)
        except Exception, e:
            self._error(e, True)
            return False
        else:
            self._message(LOG_FINISHED)
            return True

    def execute(self, commands):
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
            self.execute(['git clean -f -d -X'])
        self._message(CLEANED_UP)
        time.sleep(2)
        logs = [log for log in history() if log['build_id'] != self.stamp]
        linfo = log_info(self.stamp, self.pre_script, self.main_script)
        logs.append(linfo)
        self._save_logs(logs)
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