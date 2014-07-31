from flask import url_for, redirect, render_template, request, flash
from FlaskCI import app
from flask.ext.login import login_required
from flask_wtf import Form
from wtforms import fields, validators
import string, random

@app.route('/')
@login_required
def index():
    return render_template('index.jinja')

@app.route('/about')
def about():
    return render_template('about.jinja')

class SetupForm(Form):
    name = fields.TextField(u'CI Project Name', validators=[validators.required()])
    git_url = fields.TextField(u'Git URL', validators=[validators.required()])
    git_username = fields.TextField(u'Git Username', validators=[validators.required()])
    pw_descr = 'This must be saved as <strong>plain text</strong> on the server, therefore' \
        ' it is a good idea to set up as special user for this function.'
    git_password = fields.PasswordField(u'Git Password', validators=[validators.required()],
        description = pw_descr)
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
    script_descr = 'This is the actual test script.'
    script_dft = 'python manage.py test'
    script = fields.TextAreaField(u'Test Script', validators=[validators.required()],
        description = script_descr, default = script_dft)

    # def validate_email(self, fields):
    #     user = self.get_user()
    #     if user is None:
    #         raise validators.ValidationError('Invalid user')

    # def validate_password(self, fields):
    #     user = self.get_user()
    #     if not user.check_password(self.password.data):
    #         raise validators.ValidationError('Invalid password')


@app.route('/setup', methods=('GET', 'POST'))
@login_required
def setup():
    form = SetupForm()
    if form.validate_on_submit():
        # save the form
        flash('Settings successfully saved.')
    return render_template('setup.jinja', form = form)