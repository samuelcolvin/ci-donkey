import subprocess, shlex
from datetime import datetime as dtdt
from FlaskCI import app
import git, uuid, os, json, re, thread
import traceback, shutil, re, time, tempfile

def setup_cls():
    if os.path.exists(app.config['SETUP_FILE']):
        obj = json.load(open(app.config['SETUP_FILE'], 'r'))
        obj['datetime'] = dtdt.strptime(obj['datetime'], app.config['DATETIME_FORMAT'])
        return type('CISetup', (), obj)

def build():
    b = Build()
    thread.start_new_thread(b.build, ())
    return b.uuid

def _now():
    return dtdt.utcnow().strftime(app.config['DATETIME_FORMAT'])

def _build_log_path(id):
    return os.path.join('/tmp', id + '.log')

def get_build_log(build_id):
    return Build.log_info(build_id)

class KnownError(Exception):
    pass

class CommandError(Exception):
    pass

TERMINAL_ERROR =   '   ############# TERMINAL ERROR #############\n'
LOG_PRE_FINISHED = '   ############# PRE BUILD FINISHED #############\n'
LOG_FINISHED =     '   ############# FINISHED #############\n'
class Build(object):
    def __init__(self, delete_after = True):
        self.setup = setup_cls()
        self.uuid = str(uuid.uuid4())
        self.delete_after = delete_after
        self.log_file = _build_log_path(self.uuid)
        self._log('Starting build at %s' % _now())
        self._log('log filename: %s' % self.log_file)
        self.tmp_path = os.path.join(tempfile.gettempdir(), self.uuid)
        self._log('project directory: %s' % self.tmp_path)
        self.pre_script = []
        self.main_script = []

    def set_url(self):
        self.url = self.setup.git_url
        t = self.setup.github_token
        if len(t) > 0:
            self.url = re.sub('https://', 
                'https://%s@' % t, self.url)
        self._log('clone url: %s' % self.url.replace(t, '<token>'))

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
            self.set_url()
            self.download()
            self.execute(self.pre_script)
        except Exception, e:
            self._error(e)
            return False
        else:
            self._message(LOG_PRE_FINISHED)
            return True

    def download(self):
        git.Git().clone(self.url, self.tmp_path)
        self._log('cloned code successfully')
        config_path = os.path.join(self.tmp_path, app.config['CONFIG_SCRIPT'])
        if not os.path.exists(config_path):
            raise KnownError('Repo has config no file: %s' % app.config['CONFIG_SCRIPT'])
        config_script = open(config_path, 'r').read()
        if app.config['CONFIG_MAIN'] not in config_script:
            raise KnownError('Config has no divider: %s' % app.config['CONFIG_MAIN'])
        in_main_script = False
        for line in config_script.split('\n'):
            if app.config['CONFIG_PRE'] in line or line == '':
                continue
            if app.config['CONFIG_MAIN'] in line:
                in_main_script = True
                continue
            if in_main_script:
                self.main_script.append(line)
            else:
                self.pre_script.append(line)


    def main_build(self):
        try:
            self.execute(self.main_script)
        except Exception, e:
            self._error(e)
            return False
        else:
            self._message(LOG_FINISHED)
            return True

    def execute(self, commands):
        commands = commands.split('\n')
        for command in commands:
            if command.strip().startswith('#'):
                self._log(command, 'SKIP> ')
                continue
            self._log(command, 'EXEC> ')
            cargs = shlex.split(command)
            try:
                p = subprocess.Popen(cargs, 
                    cwd = self.tmp_path, 
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    raise CommandError(stderr)
                self._log(stdout, '')
            except CommandError, e:
                raise e
            except Exception, e:
                raise CommandError('%s: %s' % (e.__class__.__name__, str(e)))

    def _error(self, e):
        if isinstance(e, CommandError) or isinstance(e, KnownError):
            self._log('%s: %s' % (e.__class__.__name__, str(e)))
        else:
            tb = traceback.format_exc()
            self._log(tb)
        self._message(TERMINAL_ERROR)

    def _finish(self):
        time.sleep(1)
        if self.delete_after and os.path.exists(self.tmp_path):
            shutil.rmtree(self.tmp_path, ignore_errors = False)
        self._log('Build finished at %s' % _now())
        logs = []
        if os.path.exists(app.config['LOG_FILE']):
            logs = json.load(open(app.config['LOG_FILE'], 'r'))
        logs.append(Build.log_info(self.uuid))
        json.dump(logs, open(app.config['LOG_FILE'], 'w'), indent = 2)
        if self.delete_after:
            os.remove(self.log_file)

    @staticmethod
    def log_info(build_id):
        with open(_build_log_path(build_id), 'r') as logfile:
            log = logfile.read()
            datetime = re.search('Starting build at (.*)', log).groups()[0]
            prelog = log
            mainlog = None
            prefin = LOG_PRE_FINISHED in log
            if prefin:
                prelog, mainlog = prelog.split(LOG_PRE_FINISHED)
                prelog += LOG_PRE_FINISHED
            finished = LOG_FINISHED in log
            term_error = TERMINAL_ERROR in log
            status = locals()
            del status['logfile']
            return status

    def _message(self, message):
        with open(self.log_file, 'a') as logfile:
            logfile.write(message)

    def _log(self, line, prefix = '#> '):
        # print line
        with open(self.log_file, 'a') as logfile:
            logfile.write(prefix + line.strip('\n \t') + '\n')