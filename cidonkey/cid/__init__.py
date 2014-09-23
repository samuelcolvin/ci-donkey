import os
PAR_DIR = os.path.dirname(os.path.dirname(__file__))
os.chdir(PAR_DIR)
from flask import Flask, request, url_for
__version__ = '0.0.1'

app = Flask(__name__)
app.config.from_object('cid.settings')
app.jinja_env.autoescape = True

from . import ui, auth
