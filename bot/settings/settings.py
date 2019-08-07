import os
from pathlib import Path

from configurations import Configuration

BASE_PATH = Path(__file__).absolute().parent.parent.parent


class Base(Configuration):
    BASE_DIR = BASE_PATH.as_posix()

    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

    @property
    def ALLOWED_HOSTS(self):
        allowed_hosts = ['localhost', '127.0.0.1']
        for allowed_host in filter(lambda string: string.startswith('ALLOWED_HOST_'), os.environ):
            allowed_hosts.append(os.environ[allowed_host])
        return allowed_hosts

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django_telegrambot',
        'bot.apps.DjangoTelegramBotBaseConfig',
    ]

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    ROOT_URLCONF = 'bot.urls'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [(BASE_PATH / 'templates').as_posix()],

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

    WSGI_APPLICATION = 'bot.wsgi.application'

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

    LANGUAGE_CODE = 'en-us'

    TIME_ZONE = 'UTC'

    USE_I18N = True

    USE_L10N = True

    USE_TZ = True

    STATIC_URL = '/static/'
    STATIC_ROOT = (BASE_PATH / 'static').as_posix()

    MEDIA_ROOT = (BASE_PATH / 'media').as_posix()
    MEDIA_URL = '/media/'

    AVAILABLE_FONTS = os.environ['AVAILABLE_FONTS']


class Production(Base):
    DEBUG = False

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'channel_automa_prod',
            'USER': os.environ.get('DJANGO_DB_USER'),
            'PASSWORD': os.environ.get('DJANGO_DB_PASSWD'),
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

    # Telegram Bot
    DJANGO_TELEGRAMBOT = {
        'MODE': 'WEBHOOK',
        'WEBHOOK_SITE': os.environ.get('DJANGO_WEBSITE'),
        'WEBHOOK_PREFIX': 'webhook/',
        'STRICT_INIT': True,

        'BOTS': [
            {
                'TOKEN': os.environ['TELEGRAM_TOKEN'],
                'MESSAGEQUEUE_ENABLED': True,
            },
        ],

    }


class Development(Base):
    DEBUG = True

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'channel_automa_dev',
            'USER': '',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

    # Telegram Bot
    DJANGO_TELEGRAMBOT = {
        'MODE': 'POLLING',
        # We use pulling but this prevents a throwing an error on start that a url should not start with a "/"
        'WEBHOOK_PREFIX': 'webhook/',

        'STRICT_INIT': True,

        'BOTS': [
            {
                'TOKEN': os.environ['TELEGRAM_TOKEN'],
                'MESSAGEQUEUE_ENABLED': True,
            },
        ],

    }
