import subprocess
from datetime import datetime as dtdt
from FlaskCI import app
import git, uuid, os, json

def settings_cls():
    if os.path.exists(app.config['SETUP_FILE']):
        obj = json.load(open(app.config['SETUP_FILE'], 'r'))
        obj['datetime'] = dtdt.strptime(obj['datetime'], app.config['DATETIME_FORMAT'])
        return type('CISetup', (), obj)


class CI(object):
    def __init__(self):
        self.settings = settings_cls()
        self.tmp_path = os.path.join('tmp', str(uuid.uuid4()))

    def download(self):
        git.Git().clone(self.settings.git_url, self.tmp_path)