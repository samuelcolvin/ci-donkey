from flask import url_for, redirect, render_template
from flask import flash, jsonify, request, send_file
from flask.ext.login import login_required, current_user
from flask_wtf import Form
from wtforms import fields, validators
from . import app, ci, auth, github
from datetime import datetime as dtdt
from collections import OrderedDict
import string
import random
import json
import os
import traceback
import time
import pytz

def api_error(e):
    traceback.print_exc()
    return '%s: %s' % (e.__class__.__name__, str(e)), 400

@app.template_global()
def main_menu():
    ep = request.endpoint
    if not current_user.is_authenticated():
        pages = [(url_for('login_view'), 'Login')]
    else:
        if current_user.is_admin():
            pages = [(url_for('build'), 'Build Now'), (url_for('setup'), 'Setup')]#, ('about', 'About')
        else:
            pages = [(url_for('build'), 'Build Now')]#, ('about', 'About')
        setupci = ci.setup_cls()
        url = setupci.git_url if setupci else None
        if url not in ['', None]:
            pages += [(url, 'Github')]
    return [{'page': page, 'name': name, 'active': ep == page} for page, name in pages]

@app.route('/')
@login_required
def index():
    logs = ci.history()
    logs.reverse()
    records = []
    for log in logs:
        master = None
        if log['finished'] and 'master' in log and log['master']:
            master = 'glyphicon-flag'
        records.append({
            'Date': date_link(log),
            'Trigger': log.get('trigger', None),
            'Time Taken': log.get('time_taken', None),
            'Author': log.get('author', ''),
            'Master': master,
            'Test Successful': not log['term_error'] if log['finished'] else 'show-spinner',
            'Test Passed': log['test_passed'] if log['finished'] else None
        })
    theadings = ('Date', 'Time Taken', 'Trigger', 'Author', 
        'Master', 'Test Successful', 'Test Passed')
    return render_template('index.jinja', 
                            records = records, 
                            theadings = theadings)

def date_link(log):
    dt = ci.dt_from_str(log['datetime']).replace(tzinfo = pytz.utc)
    dstr = dt.astimezone(pytz.timezone('Europe/London')).strftime(app.config['DISPLAY_DT'])
    return '<a href="%s">%s</a>' % (url_for('show_build', id = log['build_id']), dstr)

@app.route('/build')
@login_required
def build():
    build_info = OrderedDict([
        ('trigger', 'manual'),
        ('author', current_user.email),
        ('master', True)
    ])
    build_id = ci.build(build_info)
    return render_template('build.jinja', pogress_url = url_for('progress', id = build_id))

@app.route('/show_build/<id>')
@login_required
def show_build(id = None):
    logs = ci.history()
    log = (log for log in logs if log['build_id'] == id).next()
    if not log['finished']:
        return render_template('build.jinja', pogress_url = url_for('progress', id = id))
    else:
        build_status = {
            'success': not log.get('term_error', False),
            'passed': log.get('test_passed', None)
        }
        return render_template('build.jinja', 
            build_status = build_status,
            pre_build_log = log.get('prelog', ''),
            main_build_log = log.get('mainlog', ''),
            pre_script = '\n'.join(log.get('pre_script', '')),
            main_script = '\n'.join(log.get('main_script', '')),
            log_extra = log
        )

@app.route('/progress/<id>')
@login_required
def progress(id = None):
    try:
        status = ci.log_info(id)
    except Exception, e:
        return api_error(e)
    else:
        return jsonify(**status)

@app.route('/secret_build/<code>', methods=('POST',))
def secret_build(code = None):
    cisetup = ci.setup_cls()
    time.sleep(0.5)
    if cisetup.secret_url != code:
        return 'Incorrect code', 403

    approved, hook_info = github.process_request(request, cisetup)
    if not approved:
        return str(hook_info), 200

    build_id = ci.build(hook_info)
    return 'building, build_id: %s' % build_id

@app.route('/status.svg')
def status_svg():
    if not os.path.exists(app.config['STATUS_SVG_FILE']):
        return 'no builds, no status file', 400
    svg_path = os.path.join('..', app.config['STATUS_SVG_FILE'])
    return send_file(svg_path, mimetype = 'image/svg+xml', cache_timeout=0)

class SetupForm(Form):
    name = fields.TextField('CI Project Name', validators=[validators.required()])

    url_descr = 'This should be the https url for github.'
    git_url = fields.TextField('Git URL', validators=[validators.required()], description = url_descr)

    this_url_descr = 'URL of this site, used for "datails" on pull request statuses.'
    this_url = fields.TextField('CI site URL', description = this_url_descr)

    token_descr = 'See <a href="https://help.github.com/articles/creating-an'\
        '-access-token-for-command-line-use">here</a> for details on how create a token. '\
        'The token needs the "repo" scope to clone private repos. Used for cloning on private repos '\
        'and for updating pull request statuses on all repos.'
    github_token = fields.TextField(u'Github Token', description = token_descr)

    allowed_hooks_descr = 'Comma seperated list of webooks to accept from github, '\
        '<a href="https://developer.github.com/v3/repos/hooks/">see here for details</a>.'\
        'Normally push and pull_request will suffice.'
    allowed_hooks = fields.TextField('Webhooks', description = allowed_hooks_descr,
        validators=[validators.required()], default = 'push, pull_request')

    dft_secret_url = ''.join(random.choice(string.ascii_lowercase + \
        string.digits + string.ascii_uppercase) for i in range(60))
    secret_url_descr = 'This will make up the url which github pings. url: http://&lt;domain&gt;/secret_build/&lt;secret&gt;'
    secret_url = fields.TextField('Secret URL Argument', description = secret_url_descr,
        validators=[validators.required()], default = dft_secret_url)

    ci_script_descr = 'This is the file which is split then ran to test the project.'
    ci_script = fields.TextField('CI Script Name', description = ci_script_descr,
        validators=[validators.required()], default = 'cidonkey.sh')

    pre_tag_descr = 'Tag signifying beginning of pre test script.'
    pre_tag = fields.TextField('Pre Script Start', description = pre_tag_descr,
        validators=[validators.required()], default = '<PRE SCRIPT>')

    main_tag_descr = 'Tag signifying beginning of main test script.'
    main_tag = fields.TextField('Main Script Start', description = main_tag_descr,
        validators=[validators.required()], default = '<MAIN SCRIPT>')

    save_repo_descr = 'If checked the cloned repo will be kept after CI is complete, otherwise it will be deleted perminently.'
    save_repo = fields.BooleanField('Save Repo', description=save_repo_descr, default=False)

    save_dir_descr = 'Directory to save copies of the repo in (only used if "Save Repo" is checked).'\
         'hould have write permissions ci-donkey user.'
    save_dir = fields.TextField('Save Directory', description=save_dir_descr)

    def validate_git_url(self, field):
        if not field.data.startswith('https://'):
            raise validators.ValidationError('git URL must start https://')

    def validate_save_dir(self, field):
        path = field.data
        if path == '':
            return
        if not os.path.exists(path):
            raise validators.ValidationError('Path must exist.')
        if not os.path.isdir(path):
            raise validators.ValidationError('Path must be a directory not a file.')
        if not os.access(path, os.W_OK):
            raise validators.ValidationError('This user does not have write permissions.')

    def dump_json(self):
        d = {}
        for atname in dir(self):
            attr = getattr(self, atname)
            if isinstance(attr, fields.Field):
                if attr.name != 'csrf_token':
                    if attr.name == 'save_dir':
                        d['save_dir'] = None if attr.data == '' else attr.data
                    elif attr.name == 'allowed_hooks':
                        d['allowed_hooks'] = [wh.strip() for wh in attr.data.split(',')]
                    else:
                        d[attr.name] = attr.data
        d['datetime'] = dtdt.utcnow().strftime(app.config['DATETIME_FORMAT'])
        json.dump(d, open(app.config['SETUP_FILE'], 'w'), indent = 2)

    @staticmethod
    def from_json():
        obj = ci.setup_cls()
        if hasattr(obj, 'allowed_hooks'):
            obj.allowed_hooks = ', '.join(obj.allowed_hooks)
        return SetupForm(obj = obj) if obj else SetupForm()


@app.route('/setup', methods=('GET', 'POST'))
@auth.admin_required
def setup():
    form = SetupForm.from_json()
    if form.validate_on_submit():
        form.dump_json()
        flash('Settings successfully saved.')
        return redirect(url_for('index'))
    return render_template('setup.jinja', form = form)

# @app.route('/about')
# def about():
#     return render_template('about.jinja')
