from flask import Flask, request, url_for
from flask.ext.login import current_user
__version__ = '0.0.1'

app = Flask(__name__)
app.config.from_object('FlaskCI.settings')

@app.template_global()
def main_menu():
    ep = request.endpoint
    if not current_user.is_authenticated():
        return [{'page': 'login_view', 'name': 'Login', 'active': ep == 'login_view'}]
    pages = [('setup', 'Setup'), ('about', 'About')]
    return [{'page': page, 'name': name, 'active': ep == page} for page, name in pages]


import FlaskCI.ui, FlaskCI.auth

# for rule in app.url_map.iter_rules():
#     print '%r' % rule