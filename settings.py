import os
BASE_DIR = os.path.dirname(__file__)

SECRET_KEY = '!!! change me in localsettings.py !!!'

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# you should set this in localsettings.py
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_jinja',
    'cidonkey'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'cidonkey.views.cid_context',
    'django.contrib.messages.context_processors.messages',
)

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

# override the DATABASE in localsettings.py to use something more powerful
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
}}

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = False
USE_TZ = True

STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'

# # To enable S3 put the following code in localsettings.py:
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# AWS_QUERYSTRING_AUTH = True
# AWS_S3_SECURE_URLS = True
# AWS_DEFAULT_ACL = 'private'
# AWS_QUERYSTRING_EXPIRE = 600
# # The following is sensitive, make sure you don't inadvertently commit it to public VC!
# AWS_ACCESS_KEY_ID = 'aws s3 key id'
# AWS_SECRET_ACCESS_KEY = 'aws s3 access key'
# AWS_STORAGE_BUCKET_NAME = 'bucket name'
# MEDIA_URL = 'https://... s3 url'

MEDIA_ROOT = 'mediafiles'
MEDIA_URL = '/media/'

TEMPLATE_LOADERS = (
    'django_jinja.loaders.FileSystemLoader',
    'django_jinja.loaders.AppLoader'
)

DEFAULT_JINJA2_TEMPLATE_EXTENSION = '.jinja'

JINJA2_ENVIRONMENT_OPTIONS = {
    'trim_blocks': True,
}

LOGIN_REDIRECT_URL = '/'

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# docker settings:
# how often the CI thread should check docker
THREAD_CHECK_RATE = 10
# delete containers after x minutes, if -1 containers will not be deleted
CONTAINER_DELETE_MINUTES = 20
PERSISTENCE_DIR = '/tmp/ci-persistence'
# whether or not to update commits' on github
SET_STATUS = True
# maximum number of simultaneous builds to allow, 1 for no concurrent builds
MAX_CONCURRENT_BUILDS = 2

# override settings locally
try:
    from localsettings import *
except ImportError:
    print 'no localsettings.py'
else:
    print 'localsettings.py imported successfully'
