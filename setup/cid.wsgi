activate_this = '/var/www/ci-donkey/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
sys.path.insert(0, '/var/www/ci-donkey')
from cid import app as application
