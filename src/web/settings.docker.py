"""
Django settings for drapo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = os.environ

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env['DJANGO_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (env.get('DJANGO_DEBUG') == 'True')

ALLOWED_HOSTS = env['ALLOWED_HOSTS'].split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'hijack',
    'hijack_admin',
    'sortedm2m',
    'markdown_deux',
    'bootstrap3_datetime',
    'bootstrapform',

    'drapo',
    'users',
    'teams',
    'contests',
    'taskbased.tasks',
    'taskbased.categories',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'drapo.middleware.LocaleMiddleware',
]

ROOT_URLCONF = 'drapo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'drapo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env['POSTGRES_DB'], # Имя базы данных
        'USER': env['POSTGRES_USER'], # Имя пользователя
        'PASSWORD': env['POSTGRES_PASSWORD'], # Поменяйте на свой пароль!
        'HOST': 'db', # Если сервер баз данных установлен на другом компьютере, укажите тут его адрес
        'PORT': 5432, # Оставьте пустым, если используется порт по умолчанию
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/users/login/'
LOGOUT_URL = '/users/logout/'


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = env.get('LANGUAGE_CODE', 'en-us')

TIME_ZONE = env.get('TIME_ZONE', 'UTC')

USE_I18N = True

USE_L10N = True

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_ROOT = '/static/'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'third-party')
]


# See hijack documentation for details: http://django-hijack.readthedocs.io/en/stable/
HIJACK_DISPLAY_ADMIN_BUTTON = False
HIJACK_LOGIN_REDIRECT_URL = '/'
HIJACK_LOGOUT_REDIRECT_URL = '/admin/users/user'
HIJACK_USE_BOOTSTRAP = True
HIJACK_REGISTER_ADMIN = False
HIJACK_ALLOW_GET_REQUESTS = True


DRAPO_TEAM_SIZE_LIMIT = 100

# By one participant in one contest
DRAPO_MAX_TRIES_IN_MINUTE = int(env.get('DRAPO_MAX_TRIES_IN_MINUTE', '10'))

DRAPO_EMAIL_SENDER = env.get('DRAPO_EMAIL_SENDER', 'nobody@localhost')
DRAPO_UPLOAD_DIR = '/upload'
DRAPO_TASKS_FILES_DIR = os.path.join(DRAPO_UPLOAD_DIR, 'tasks_files')

DRAPO_TEAM_NAMES_ARE_UNIQUE = False
DRAPO_USER_CAN_BE_ONLY_IN_ONE_TEAM = False
# If False captain can edit team name
DRAPO_ONLY_STAFF_CAN_EDIT_TEAM_NAME = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

#Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = env.get('EMAIL_HOST')
EMAIL_PORT = int(env.get('EMAIL_PORT', '0'))
EMAIL_HOST_USER = env.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = env.get('DEFAULT_FROM_EMAIL', DRAPO_EMAIL_SENDER)
