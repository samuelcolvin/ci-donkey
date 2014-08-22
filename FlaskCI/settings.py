DEBUG = False
SECRET_KEY = '!! change or overwrite me !!'
USER_FILE = 'users.json'
SETUP_FILE = 'setup.json'
LOG_FILE = 'log.json'
STATUS_SVG_FILE = 'status.svg'
SITE_TITLE = 'Flask CI'
DATETIME_FORMAT = '%a, %d-%b-%Y %H:%M:%S UTC'
DISPLAY_DT = '%a, %d-%b-%y %H:%M'
# you should overwrite SECRET_KEY in localsettings.py
try:
    from localsettings import *
except ImportError:
    pass
