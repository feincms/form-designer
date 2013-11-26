import os

SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'testapp',
    'feincms',
    'feincms.module.page',
    'form_designer',
]

MEDIA_ROOT = '/media/'
STATIC_URL = '/static/'
BASEDIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASEDIR, 'media/')
STATIC_ROOT = os.path.join(BASEDIR, 'static/')
SECRET_KEY = 'supersikret'
LOGIN_REDIRECT_URL = '/?login=1'

ROOT_URLCONF = 'testapp.urls'
LANGUAGES = (('en', 'English'), ('de', 'German'))
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)

DEFAULT_FROM_EMAIL = 'no-reply@example.com'
