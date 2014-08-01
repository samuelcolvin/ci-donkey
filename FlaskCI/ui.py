from flask import url_for, redirect, render_template
from flask import flash, jsonify, request, send_file
from FlaskCI import app
from flask.ext.login import login_required
from flask_wtf import Form
from wtforms import fields, validators
import string, random, json, os, traceback, time, pytz
from datetime import datetime as dtdt
import ci

def api_error(e):
    traceback.print_exc()
    return '%s: %s' % (e.__class__.__name__, str(e)), 400

@app.route('/')
@login_required
def index():
    logs = ci.Build.history()
    logs.reverse()
    records = []
    for log in logs:
        records.append({
            'Date': date_link(log),
            'Complete': html_bool(log['finished']),
            'Test Successful': html_bool(not log['term_error']),
            'Test Passed': html_bool(log['test_passed'])
            })
    theadings = ('Date', 'Complete', 'Test Successful', 'Test Passed')
    return render_template('index.jinja', records = records, theadings = theadings)

def date_link(log):
    dt = ci.dt_from_str(log['datetime']).replace(tzinfo = pytz.utc)
    dstr = dt.astimezone(pytz.timezone('Europe/London')).strftime(app.config['DISPLAY_DT'])
    return '<a href="%s">%s</a>' % (url_for('show_build', id = log['build_id']), dstr)

def html_bool(b):
    glyph = 'ok' if b else 'remove'
    return '<span class="glyphicon glyphicon-%s"></span>' % glyph

@app.route('/build')
@login_required
def build():
    build_id = ci.build()
    return render_template('build.jinja', pogress_url = url_for('progress', id = build_id))

@app.route('/show_build/<id>')
@login_required
def show_build(id = None):
    logs = ci.Build.history()
    log = (log for log in logs if log['build_id'] == id).next()
    if not log['finished']:
        return render_template('build.jinja', pogress_url = url_for('progress', id = id))
    else:
        build_status =  '<p>Test Status: %s</p>\n' % html_bool(not log['term_error'])
        build_status += '<p>Test Passed: %s</p>' % html_bool(log['test_passed'])
        return render_template('build.jinja', 
            build_status = build_status,
            pre_build_log = log['prelog'],
            main_build_log = log['mainlog'],
            pre_script = '\n'.join(log['pre_script']),
            main_script = '\n'.join(log['main_script']))

@app.route('/progress/<id>')
@login_required
def progress(id = None):
    try:
        status = ci.Build.log_info(id)
    except Exception, e:
        return api_error(e)
    else:
        return jsonify(**status)

@app.route('/secret_build/<code>')
def secret_build(code = None):
    setup = obj = ci.setup_cls()
    print 'request.data:', request.data
    time.sleep(0.5)
    if setup.secret_url != code:
        return 'Incorrect code', 403
    build_id = ci.build()
    return 'building, build_id: %s' % build_id

@app.route('/status.svg')
def status_svg():
    if not os.path.exists(app.config['STATUS_SVG_FILE']):
        return 'no builds, no status file', 400
    svg_path = os.path.join('..', app.config['STATUS_SVG_FILE'])
    return send_file(svg_path, mimetype = 'image/svg+xml')

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

    ci_script_descr = 'This is the file which is split then ran to test the project.'
    ci_script = fields.TextField(u'CI Script Name', description = ci_script_descr,
        validators=[validators.required()], default = 'FlaskCI.sh')

    pre_tag_descr = 'Tag signifying beginning of pre test script.'
    pre_tag = fields.TextField(u'CI Script Name', description = pre_tag_descr,
        validators=[validators.required()], default = '<PRE SCRIPT>')

    main_tag_descr = 'Tag signifying beginning of main test script.'
    main_tag = fields.TextField(u'CI Script Name', description = main_tag_descr,
        validators=[validators.required()], default = '<MAIN SCRIPT>')

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