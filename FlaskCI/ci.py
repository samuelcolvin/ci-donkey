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
    pw_descr = 'This must be saved as plain text on the server, therefore' \
        ' its a good idea to set up as special user for this function.'
    git_password = fields.PasswordField(u'Git Password', validators=[validators.required()],
        description = pw_descr)
    dft_secret_url = ''.join(random.choice(string.ascii_lowercase + \
        string.digits + string.ascii_uppercase) for i in range(60))
    secret_url_descr = 'This will make up the which github pings after a push.'
    secret_url = fields.TextField(u'Secret URL Argument', description = secret_url_descr,
        validators=[validators.required()], default = dft_secret_url)

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