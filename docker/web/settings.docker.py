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
    'serialization',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'drapo.middleware.log_requests_middleware',
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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env['POSTGRES_DB'], # Имя базы данных
        'USER': env['POSTGRES_USER'], # Имя пользователя
        'PASSWORD': env['POSTGRES_PASSWORD'], # Поменяйте на свой пароль!
        'HOST': env['POSTGRES_HOST'], # Если сервер баз данных установлен на другом компьютере, укажите тут его адрес
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
    'loggers': {
        'drapo.requests': {
            'handlers': ['drapo.requests'],
            'level': 'INFO',
        },
    },
    'handlers': {
        'drapo.requests': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'drapo.requests',
        },
    },
    'formatters': {
        'drapo.requests': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(server_time)s] %(message)s',
        }
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

# For serving files with nginx, disabled by default
DRAPO_SENDFILE_WITH_NGINX = False
DRAPO_SENDFILE_ROOT = os.path.abspath(DRAPO_UPLOAD_DIR)
DRAPO_SENDFILE_URL = '/protected'

LANGUAGES = [
    ('ru', 'Russian'),
    ('en', 'English'),
]

MARKDOWN_DEUX_STYLES = {
    'default': {
        'extras': {
            'code-friendly': None,
        },
        'safe_mode': False if env.get('MARKDOWN_DISABLE_SAFE_MODE') == 'True' else 'escape',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached:11211',
        'OPTIONS': {
            'server_max_value_length': 1024 * 1024 * 8,
        }
    }
}


QCTF_CONTEST_ID = 1

QCTF_CARD_LAYOUT = [
    [
        ('permanent-302', '/static/statement_img/podifruxx.png'),
        ('storage', '/static/statement_img/smvcnid.png'),
    ],
    [
        ('make-some-noise', None),
        ('cipher', None),
        ('weird-video', None),
    ],
    [
        ('getflagchar', '/static/statement_img/gohdjhr.png'),
        ('minecrypt', '/static/statement_img/msslrrijc.png'),
    ],
    [
        ('unpack-reverse', None),
        ('cats-vs-dogs', None),
        ('notemaster', None),
    ],
    [
        ('bank', '/static/statement_img/blfpowdm.png'),
        ('passengers-1', '/static/statement_img/psgrttry.png'),
    ],
    [
        ('browser-mining', None),
        ('auth-system', None),
        ('obscure-archive', None),
    ],
    [
        ('passengers-2', None),
        ('python-vm', None),
        ('quirky-casino', None),
    ],
]

# Place tasks ordered by cost. They will be shown in the QCTF scoreboard in the same order.
QCTF_TASK_CATEGORIES = {
    'Crypto': ['cipher', 'minecrypt'],
    'Forensics': ['weird-video', 'bank'],
    'PPC': ['quirky-casino', 'browser-mining', 'cats-vs-dogs'],
    'PWN': ['passengers-1', 'passengers-2'],
    'Reverse': ['getflagchar', 'obscure-archive', 'unpack-reverse', 'python-vm'],
    'Web': ['notemaster', 'permanent-302', 'make-some-noise', 'storage', 'auth-system'],
}
