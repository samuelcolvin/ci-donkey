from flask import url_for, redirect, render_template, flash, jsonify
from FlaskCI import app
from flask.ext.login import login_required
from flask_wtf import Form
from wtforms import fields, validators
import string, random, json, os, traceback
from datetime import datetime as dtdt
from pprint import pprint
import ci

def api_error(e):
    traceback.print_exc()
    return '%s: %s' % (e.__class__.__name__, str(e)), 400

@app.route('/')
@login_required
def index():
    return render_template('index.jinja')

@app.route('/build')
@login_required
def build():
    build_id = ci.build()
    return render_template('build.jinja', pogress_url = url_for('progress', id = build_id))

@app.route('/progress/<id>')
@login_required
def progress(id = None):
    try:
        status = ci.Build.log_info(id)
    except Exception, e:
        return api_error(e)
    else:
        return jsonify(**status)

class SetupForm(Form):
    name = fields.TextField(u'CI Project Name', validators=[validators.required()])

    url_descr = 'This should be the https url for github.'
    git_url = fields.TextField(u'Git URL', validators=[validators.required()], description = url_descr)

    token_descr = 'See <a href="https://help.github.com/articles/creating-an'\
        '-access-token-for-command-line-use">here</a> for details on how create a token. '\
        'The token needs the "repo" scope to clone private repos. Leave blank for public repos.'
    github_token = fields.TextField(u'Github Token', description = token_descr)

    dft_secret_url = ''.join(random.choice(string.ascii_lowercase + \
        string.digits + string.ascii_uppercase) for i in range(60))
    secret_url_descr = 'This will make up the which github pings after a push.'
    secret_url = fields.TextField(u'Secret URL Argument', description = secret_url_descr,
        validators=[validators.required()], default = dft_secret_url)

    pre_script_descr = 'This is run after clone and changing into the project directory, ' \
        'but is not part of the test, failure will be considered setup failure not CI failure'
    pre_script_dft = 'virtualenv env\nenv/bin/pip install -r requirements.txt'
    pre_script = fields.TextAreaField(u'Pre Test Script', validators=[validators.required()],
        description = pre_script_descr, default = pre_script_dft)

    script_descr = 'This is the actual test script. Comment out commands with a #.'
    script_dft = 'python manage.py test'
    script = fields.TextAreaField(u'Test Script', validators=[validators.required()],
        description = script_descr, default = script_dft)

    def dump_json(self):
        d = {}
        for atname in dir(self):
            attr = getattr(self, atname)
            if isinstance(attr, fields.Field):
                if attr.name != 'csrf_token':
                    d[attr.name] = attr.data
        d['datetime'] = dtdt.utcnow().strftime(app.config['DATETIME_FORMAT'])
        json.dump(d, open(app.config['SETUP_FILE'], 'w'), indent = 2)

    @staticmethod
    def from_json():
        obj = ci.setup_cls()
        return SetupForm(obj = obj) if obj else SetupForm()


@app.route('/setup', methods=('GET', 'POST'))
@login_required
def setup():
    form = SetupForm.from_json()
    if form.validate_on_submit():
        form.dump_json()
        flash('Settings successfully saved.')
        return redirect(url_for('index'))
    return render_template('setup.jinja', form = form)

@app.route('/about')
def about():
    return render_template('about.jinja')