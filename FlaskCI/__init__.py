from flask import Flask, request, url_for
__version__ = '0.0.1'

app = Flask(__name__)
app.config.from_object('FlaskCI.settings')
app.jinja_env.autoescape = True

from . import ui, auth