from flask import url_for, redirect, request, render_template, flash
from flask_wtf import Form
from wtforms import fields, validators
from flask.ext import login
from werkzeug.security import generate_password_hash, check_password_hash
from FlaskCI import app
import os, json, uuid
from pprint import pprint

class UserManager(object):
    def __init__(self, model):
        print 'loading users'
        self.model = model
        self._objs = []
        self._obj_file = app.config['USER_FILE']
        if os.path.exists(self._obj_file):
            self._objs = self._load()

    def get(self, **kwargs):
        for obj in self._objs:
            if all(item in obj.items() for item in kwargs.items()):
                return obj

    def filter(self, **kwargs):
        return [obj for obj in self._objs if 
            all(item in obj.items() for item in kwargs.items())]

    def add_item(self, item):
        current = self.get(uuid = item.uuid)
        if current:
            self._objs.remove(current)
        self._objs.append(item)

    def save(self):
        json.dump(self._objs, open(self._obj_file, 'w'), indent = 2, cls = UserManager.Encoder)

    def _load(self):
        return json.load(open(self._obj_file, 'r'), object_hook = self.decode)

    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, User):
                return obj.__dump__()
            return json.JSONEncoder.default(self, obj)

    def decode(self, dct):
        if self.model.__isinstance__(dct):
            return self.model.__load__(dct)
        return dct

    def __len__(self):
        return len(self._objs)

class User():
    _serialise = ['email', 'uuid', 'active', 'hash']
    _ser_marker = 'UserObject'
    invalid = 'INVALID'

    def __init__(self, email = None, password = None):
        self.email = email
        self.uuid = unicode(uuid.uuid4())
        self.active = False
        self.set_password(password)

    def set_password(self, password):
        if password is None:
            self.hash = self.invalid
        else:
            self.hash = generate_password_hash(password)

    def check_password(self, password):
        if self.hash == self.invalid:
            return False
        return check_password_hash(self.hash, password)

    def save(self):
        users.add_item(self)
        users.save()

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.uuid

    def items(self):
        return self._attr_dict().items()

    def _attr_dict(self):
        return {a: getattr(self, a) for a in self._serialise}

    def __dump__(self):
        obj = self._attr_dict()
        obj['type'] = self._ser_marker
        return obj

    @staticmethod
    def __load__(data):
        user = User()
        for a in [a for a in User._serialise if a in data]:
            setattr(user, a, data[a])
        return user

    @staticmethod
    def __isinstance__(data):
        return data.get('type', None) == User._ser_marker

    def __unicode__(self):
        return self.email

users = UserManager(User)

if len(users) == 0:
    u = User('samuel@example.com', 'testing')
    u.active = True
    u.save()

class LoginForm(Form):
    email = fields.TextField(validators=[validators.required(), validators.Email()])
    password = fields.PasswordField(validators=[validators.required()])
    _user = None

    def validate_email(self, fields):
        user = self.get_user()
        if user is None:
            raise validators.ValidationError('Invalid user')

    def validate_password(self, fields):
        user = self.get_user()
        if not user.check_password(self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        if not self._user:
            self._user = users.get(email=self.email.data)
        return self._user

@app.route('/login', methods=('GET', 'POST'))
def login_view():
    form = LoginForm()
    if form.validate_on_submit():
        user = form.get_user()
        if not user.is_active():
            flash('Account not active, please contact admins to activate your account.')
            return redirect(url_for('about'))
        login.login_user(user)
    if login.current_user.is_authenticated():
        flash('Logged in successfully.')
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.jinja', form = form, page_title = 'login')

class RegistrationForm(Form):
    email = fields.TextField(validators=[validators.required(), validators.Email()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if len(users.filter(email=self.email.data)) > 0:
            raise validators.ValidationError('Duplicate username')

@app.route('/logout')
@login.login_required
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))

login_manager = login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_view'

@login_manager.user_loader
def load_user(user_id):
    return users.get(uuid = user_id)


# # Create customized index view class that handles login & registration
# class MyAdminIndexView(admin.AdminIndexView):

#     @expose('/')
#     def index(self):
#         if not login.current_user.is_authenticated():
#             return redirect(url_for('.login_view'))
#         return super(MyAdminIndexView, self).index()

#     @expose('/login/', methods=('GET', 'POST'))
#     def login_view(self):
#         # handle user login
#         form = LoginForm(request.form)
#         if helpers.validate_form_on_submit(form):
#             user = form.get_user()
#             login.login_user(user)

#         if login.current_user.is_authenticated():
#             return redirect(url_for('.index'))
#         link = '<p>Don\'t have an account? <a href='' + url_for('.register_view') + ''>Click here to register.</a></p>'
#         self._template_args['form'] = form
#         self._template_args['link'] = link
#         return super(MyAdminIndexView, self).index()

#     @expose('/register/', methods=('GET', 'POST'))
#     def register_view(self):
#         form = RegistrationForm(request.form)
#         if helpers.validate_form_on_submit(form):
#             user = User()

#             form.populate_obj(user)
#             user.password = generate_password_hash(form.password.data)
#             user.active = False

#             db.session.add(user)
#             db.session.commit()

#             login.login_user(user)
#             return redirect(url_for('.index'))
#         link = '<p>Already have an account? <a href='' + url_for('.login_view') + ''>Click here to log in.</a></p>'
#         self._template_args['form'] = form
#         self._template_args['link'] = link
#         return super(MyAdminIndexView, self).index()

#     @expose('/logout/')
#     def logout_view(self):
#         login.logout_user()
#         return redirect(url_for('.index'))



# # Create admin
# admin = admin.Admin(app, 
#                     'Auth', 
#                     index_view = MyAdminIndexView(), 
#                     base_template = 'users.jinja',
#                     template_mode = 'bootstrap3')

# Add view
# admin.add_view(MyModelView(User, db.session))

# @app.before_first_request
# def setup_db():
#     app_dir = os.path.realpath(os.path.dirname(__file__))
#     database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
#     if os.path.exists(database_path):
#         return
#     db.drop_all()
#     db.create_all()
#     test_user = User(email = 'samuel@tutorcruncher.com', 
#                      password = generate_password_hash('test'),
#                      active = True)
#     db.session.add(test_user)

#     db.session.commit()
#     return